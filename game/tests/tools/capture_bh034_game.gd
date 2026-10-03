extends Node
## bh-034 evidence in the real game: an Ascendant piece of every tier dropped on the ground at night (sigil, pillar,
## motes, the moving light over the model), the hero wearing a Primordial set in the world, each signature power
## answering on a monster, and the item tooltip.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_bh034_game.tscn -- --class=knight --slot=96 --out=<dir>

var out := ""
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	if out == "":
		out = ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-034/evidence/game")
	DirAccess.make_dir_recursive_absolute(out)
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(30)
	p = Game.player as Player
	Game.god_mode = true
	await _go(&"ruined_forest")
	await _skip()
	for e in get_tree().get_nodes_in_group(&"enemy"):
		(e as Node).queue_free()
	var at := _ground(Vector3(-56.0, 0, 12.0))
	p.teleport_to(at + Vector3.UP * 0.2)
	await _wait(40)
	# one piece of every tier in an arc in front of the hero
	var r := RandomNumberGenerator.new()
	r.seed = 34
	var ids := [&"asc_starfall_vanguard_weapon", &"asc_seraph_paladin_helm", &"asc_chronoguard_armor", &"asc_worldforger_shield"]
	for i in ids.size():
		var it := DB.make_item(ids[i], BH.Rarity.COMMON, 110, r.randi())
		Loot.spawn_item(it, at + Vector3(0, 0, -1.0), PI + 0.55 + i * 0.68, 3.2)
	await _wait(150)
	Game.ui_root.visible = false
	await _shot("drops_night")
	Game.ui_root.visible = true
	await _shot("drops_night_hud")
	# the hero in a full Primordial set
	var map := {&"helm": "helm", &"armor": "armor", &"inner_garment": "inner", &"leggings": "leggings", &"gloves_1": "gloves",
		&"gloves_2": "gloves", &"boots_1": "boots", &"boots_2": "boots", &"main_weapon": "weapon", &"accessory_1": "accessory"}
	for slot in map:
		p.hero.equipment.slots[slot] = DB.make_item(DataAscendant.piece_id(&"titanblood_champion", map[slot]), BH.Rarity.COMMON, 110, r.randi())
	p.hero.equipment.slots[&"sub_weapon"] = DB.make_item(&"asc_titanblood_champion_shield", BH.Rarity.COMMON, 110, r.randi())
	p.refresh_equipment_visuals()
	p.rebuild_stats()
	for d in get_tree().get_nodes_in_group(&"interactable"):
		if d is LootDrop:
			(d as Node).queue_free()
	await _wait(60)
	Game.ui_root.visible = false
	await _shot("hero_primordial")
	# the four signature powers, on a monster in front of the hero
	var def: EnemyDef = DB.enemies.values().filter(func(d): return d.archetype != &"boss")[0]
	var foe := Spawner.spawn_enemy(Game.current_map, def, 100, [], p.global_position + Vector3(0, 0, -3.0), {})
	await _wait(10)
	for flag in Player.ASCENDANT_FLAGS:
		p.stats.flags[flag] = 99.0
		var res := DamageResult.new()
		res.total = 400.0
		res.components = {Elements.PHYSICAL: 400.0}
		p._asc_ready.clear()
		for k in 30:
			p._ascendant_procs(foe, res)
			if p._asc_ready.has(flag):
				break
		await _wait(8)
		await _shot("proc_" + String(flag))
		p.stats.flags.erase(flag)
		await _wait(40)
	Game.ui_root.visible = true
	# the tooltip of a Primordial piece
	var tip := Tips.item(p.hero.equipment.get_item(&"armor"))
	Game.ui_root.add_child(tip)
	tip.position = Vector2(80, 60)
	await _wait(20)
	await _shot("tooltip_primordial")
	get_tree().quit()

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("SHOT ", label)

func _ground(at: Vector3) -> Vector3:
	var q := PhysicsRayQueryParameters3D.create(at + Vector3(0, 30, 0), at - Vector3(0, 30, 0), BH.LAYER_WORLD | BH.LAYER_GROUND)
	var hit := p.get_world_3d().direct_space_state.intersect_ray(q)
	return (hit.position as Vector3) if not hit.is_empty() else at

func _skip() -> void:
	for k in 40:
		await _wait(15)
		if CutscenePlayer.is_playing():
			CutscenePlayer.active.skip_all()
		elif k > 8:
			return

func _go(map_id: StringName) -> void:
	if Game.current_map_id == map_id:
		return
	Game.travel(map_id, &"start")
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(40)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
