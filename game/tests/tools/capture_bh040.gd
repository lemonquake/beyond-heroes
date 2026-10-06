extends Node
## bh-040 captures (the Descent), on a hero loaded from a hidden slot (copy a save to slot_97.json first):
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh040.tscn -- --load --slot=97 --phase=hud [--out=<dir>]
## Phases: hud (badge, its tooltip, the experience tooltip), fight (a Descent elite pack, then a boss), death (the fall's
## price), circle (a level-up into a new Circle), guide (the Field Guide's Descent section).

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/bh-040/shots")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _run() -> void:
	for i in 1200:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(2.5)
	match String(args.get("phase", "hud")):
		"hud": await _hud()
		"fight": await _fight()
		"death": await _death()
		"circle": await _circle()
		"guide": await _guide()
	get_tree().quit()

func _hud() -> void:
	var hud: Hud = Game.ui_root.hud if Game.ui_root else null
	await _shot("descent_hud")
	if hud and hud._descent_label:
		TooltipLayer.show_for(hud._descent_label, func() -> Control: return Tips.text(Descent.summary(Game.hero.progress.level), "The Descent"))
		await _wait(0.6)
		await _shot("descent_tooltip")
		TooltipLayer.hide_for(hud._descent_label)
		await _wait(0.3)
	if hud and hud._xp_label:
		TooltipLayer.show_for(hud._xp_label, hud._xp_tip)
		await _wait(0.6)
		await _shot("descent_xp_tooltip")

func _fight() -> void:
	var p := Game.player as Player
	var lvl := Game.hero.progress.level
	var spawner := Game.current_map.get_node_or_null("Spawner") as Spawner
	var diff: Dictionary = spawner.difficulty if spawner else Descent.fight(DataEnemies.DIFFICULTY[1], lvl)
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.global_position.distance_to(p.global_position) < 30.0:
			e.queue_free()
	await _wait(0.3)
	var rng := RandomNumberGenerator.new()
	rng.seed = 40
	var ahead := p.global_position + p.forward() * 7.0
	var ids := [&"glyphbound_warrior", &"coil_shaman", &"glyphbound_warrior", &"glyphbound_warrior", &"coil_shaman"]
	for i in ids.size():
		var mods: Array = Spawner.roll_elite_mods(rng, lvl) if i == 0 else []
		var at := ahead + Vector3(cos(TAU * i / ids.size()), 0, sin(TAU * i / ids.size())) * 2.5
		var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(ids[i]), lvl, mods, at, diff)
		e.alert_to(p.global_position)
	p.aim_override = ahead
	for k in 4:
		for sid in Game.hero.skill_bar:
			if sid != &"" and p.skill_block_reason(sid) == "":
				p._start_skill(sid)
				break
		await _wait(0.9)
	await _shot("descent_elite_pack")
	await _wait(2.0)
	await _shot("descent_elite_pack_2")
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy:
			e.queue_free()
	await _wait(0.5)
	var boss := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"astrarch"), lvl, [], p.global_position + p.forward() * 9.0, diff)
	boss.alert_to(p.global_position)
	p.aim_override = boss.global_position
	for k in 8:
		p.aim_override = boss.global_position + Vector3.UP
		for sid in Game.hero.skill_bar:
			if sid != &"" and p.skill_block_reason(sid) == "":
				p._start_skill(sid)
				break
		await _wait(0.8)
	await _shot("descent_boss")
	await _wait(3.0)
	await _shot("descent_boss_2")

func _death() -> void:
	var p := Game.player as Player
	var feathers := Game.hero.inventory.count_of(&"phoenix_feather")
	if feathers > 0:
		Game.hero.inventory.consume(&"phoenix_feather", feathers)
	p.hp = 1.0
	p.die(null)
	await _wait(3.2)
	await _shot("descent_death")

func _circle() -> void:
	var pr := Game.hero.progress
	var want := (Descent.circle(pr.level) * Descent.CIRCLE_SPAN) + Descent.FROM + 1
	pr.add_xp(maxi(0, XpCurve.total_xp_for_level(want) - XpCurve.total_xp_for_level(pr.level) - pr.xp))
	await _wait(0.8)
	await _shot("descent_new_circle")

func _guide() -> void:
	var w := Game.ui_root.window(&"guide") as GuideWindow
	w.open_on(4)
	await _wait(1.0)
	for c in w._content.get_children():
		if c is Label and (c as Label).text.begins_with("The Descent"):
			w._scroll.ensure_control_visible(c)
			await _wait(0.2)
			w._scroll.scroll_vertical = int((c as Control).position.y) - 20
			break
	await _wait(0.6)
	await _shot("descent_guide")

func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("SHOT ", name)
