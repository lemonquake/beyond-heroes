extends Node
## bh-012 evidence run (real renderer, real boot scene with HUD): each dungeon theme's five monsters lined up on their
## own floor, a live fight on a dungeon floor, the surface gates, a Relic Cache reveal, the summon page and a ten-call
## reveal, and a named-gear tooltip.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh012.tscn -- --class=knight --slot=97 --map=dg_deeps_1 --spawn=arrival --level=14 --out=<dir>
## Optional --only=bestiary,fight,gates,relic,summon,tooltip

var args := {}
var out := ""
var main: Node
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-012/evidence/captures")))
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
	if _want("bestiary"):
		await _bestiary()
	if _want("fight"):
		await _fight()
	if _want("gates"):
		await _gates()
	if _want("relic"):
		await _relic()
	if _want("summon"):
		await _summon()
	if _want("tooltip"):
		await _tooltip()
	print("BH012 CAPTURE DONE -> ", out)
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
	print("BH012 SHOT ", label)

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

func _bestiary() -> void:
	for d in DataDungeons.ORDER:
		await _go(DataDungeons.map_id(d, 1), &"arrival")
		await _clear_enemies()
		var arr := _open_spot(d)
		p.global_position = arr + Vector3(0, 0.05, 3.2)
		var dd := DataDungeons.get_def(d)
		var boss: StringName = dd.boss
		var themed: Array = []
		for x: EnemyDef in DataEnemiesDungeon.defs():
			if x.id != boss and (dd.pools.a.has(x.id) or dd.pools.b.has(x.id) or dd.pools.seal.has(x.id)):
				themed.append(x.id)
		var made := await _lineup(themed, arr + Vector3(0, 0, 0.5), 10)
		await _shot("bestiary_%s" % d, 240)
		for e in made:
			e.queue_free()
		await _wait(3)
		var b := await _lineup([boss], arr + Vector3(0, 0, -1.0), 12)
		p.global_position = arr + Vector3(0, 0.05, 4.5)
		await _shot("boss_%s" % d, 60)
		for e in b:
			e.queue_free()

func _fight() -> void:
	for id in [&"dg_deeps_2", &"dg_ember_2"]:
		await _go(id, &"arrival")
		var zone: Node3D = Game.current_map.find_child("EnemyZone_camp_0", true, false)
		if zone:
			p.global_position = zone.global_position + Vector3(0, 0.3, 5.0)
		await _wait(90)
		await _shot("fight_%s" % id, 10)

func _gates() -> void:
	for d in [&"warren", &"deeps"]:
		var sf: Dictionary = DataDungeons.get_def(d).surface
		await _go(sf.map, DataDungeons.gate_id(d))
		await _shot("gate_%s" % d, 30)

func _relic() -> void:
	RelicCache.open(Game.hero, 2, p)
	await _wait(30)
	var w := Game.ui_root.window(&"gacha_reveal") as GachaRevealWindow
	await _shot("relic_sealed", 10)
	w._auto = true
	await _wait(240)
	await _shot("relic_revealed", 10)
	w.close_window()
	await _wait(20)

func _summon() -> void:
	TempoGacha.add_embers(Game.hero, 200)
	var cw := Game.ui_root.window(&"tempo_caller") as TempoCallerWindow
	cw.open_on(&"summon")
	await _shot("summon_page", 30)
	cw._summon(10)
	var w := Game.ui_root.window(&"gacha_reveal") as GachaRevealWindow
	await _wait(400)
	await _shot("summon_ten_revealed", 10)
	w.close_window()
	await _wait(20)
	cw.open_on(&"hall")
	await _shot("spirit_hall", 30)
	cw.close_window()
	await _wait(20)

func _tooltip() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 1234
	var cards := HBoxContainer.new()
	cards.add_theme_constant_override("separation", 24)
	cards.position = Vector2(60, 90)
	for pair in [[&"iron_longsword", BH.Rarity.LEGENDARY], [&"iron_longsword", BH.Rarity.MASTER], [&"iron_longsword", BH.Rarity.ELITE]]:
		var it := ItemGenerator.generate(DB.item_base(pair[0]), 18, pair[1], r)
		cards.add_child(Tips.item(it, {}))
		Loot.spawn_item(it, p.global_position, r.randf() * TAU, 2.0)
	var layer := CanvasLayer.new()
	layer.layer = 50
	add_child(layer)
	layer.add_child(cards)
	await _shot("named_gear_tooltips", 60)
	layer.queue_free()
	await _shot("named_gear_on_ground", 10)
