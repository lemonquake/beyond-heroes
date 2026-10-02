extends Node
## bh-033 progress captures from the real game (Forward+ by default). Hidden save slot 95; settings are not written.
##   godot --path game res://tests/tools/capture_bh033.tscn -- --class=knight --level=12 --map=sanctuary --slot=95 \
##       --set=gear --w=1600 --h=900 --out=<dir>
## --set: gear (crafting hints, resistance limit, item tooltips), rank (next-rank tracker states), town (route views).

var args := {}
var out := ""
var main: Node
var notes := {"shots": []}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/world-polish-20261003/captures")))
	DirAccess.make_dir_recursive_absolute(out)
	Game.save_slot = 95
	Settings.resolution = 0
	Settings.window_mode = 0
	main = load("res://src/main.tscn").instantiate()
	add_child(main)
	_run.call_deferred()

func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds, true).timeout

func _shot(label: String) -> void:
	await _wait(0.6)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	notes.shots.append({"name": label, "size": [img.get_width(), img.get_height()]})
	print("SHOT ", label, " ", img.get_size())

func _run() -> void:
	await _wait(2.0)
	for i in 300:
		if Game.in_session and Game.player is Player and (Game.player as Player).hero:
			break
		await _wait(0.1)
	await _wait(1.5)
	get_window().size = Vector2i(int(args.get("w", "1600")), int(args.get("h", "900")))
	await _wait(1.0)
	notes["engine"] = Engine.get_version_info().string
	notes["renderer"] = RenderingServer.get_current_rendering_method()
	notes["adapter"] = RenderingServer.get_video_adapter_name()
	notes["window"] = [get_window().size.x, get_window().size.y]
	notes["touch"] = Settings.touch_mode
	notes["revision"] = "f7109cfd + bh-033 working tree"
	match String(args.get("set", "gear")):
		"gear": await _gear()
		"rank": await _rank()
		"creatures": await _creatures()
		"town": await _town()
		"tavern": await _tavern()
		"warden": await _warden()
		"verdigast": await _verdigast()
		_: pass
	var f := FileAccess.open(out.path_join("notes_%s.json" % args.get("set", "gear")), FileAccess.WRITE)
	f.store_string(JSON.stringify(notes, "  "))
	f.close()
	get_tree().quit()

func _float(c: Control, at: Vector2) -> Node:
	var layer := CanvasLayer.new()
	layer.layer = 120
	add_child(layer)
	layer.add_child(c)
	c.position = at
	return layer

func _gear() -> void:
	var ui: UIRoot = Game.ui_root
	var hero := Game.hero
	# a few shards in the bag, no steel yet: the forge shows what is missing and where it comes from
	var iron := DB.make_item(&"iron_shard", BH.Rarity.COMMON, 1, 1)
	iron.count = 3
	hero.inventory.add(iron)
	hero.inventory.gold = 400
	var cw := ui.window(&"crafting") as CraftingWindow
	cw.open_station(&"forge", "Brannoc's Forge")
	await _wait(0.5)
	for i in cw._recipes.size():
		if cw._recipes[i].id == &"tempered_weapon":
			cw._sel = i
	cw._show_page()
	await _shot("gear_01_forge_hints")
	for i in cw._recipes.size():
		if cw._recipes[i].id == &"steel_ingot":
			cw._sel = i
	cw._show_page()
	await _shot("gear_02_forge_steel_from_iron")
	ui.close_all()
	await _wait(0.3)
	# a deliberately stacked legacy-style fire build: the breakdown shows the equipment limit
	for slot in [&"helm", &"armor", &"inner_garment", &"leggings", &"boots_1"]:
		var cat: StringName = StringName(String(slot).split("_")[0]) if slot != &"inner_garment" else slot
		var base := ItemGenerator.random_base(TestCase.rng(hash(String(slot))), 40, [cat], &"knight", 1.0)
		var it := ItemGenerator.generate(base, 40, BH.Rarity.MASTER, TestCase.rng(hash(String(slot)) + 1))
		it.affixes = [{"id": "res_fire", "tier": 2, "value": 0.28}]
		it.sockets = 2
		it.gems = ["ember_crystalline", "sora_shard"]
		hero.equipment.slots[slot] = it
	hero.equipment.changed.emit()
	var d := hero.compute_stats()
	var layer := _float(Tips.stat(&"res_fire", d), Vector2(560, 60))
	await _shot("gear_03_fire_resistance_equipment_limit")
	layer.queue_free()
	var sample := ItemGenerator.generate(ItemGenerator.random_base(TestCase.rng(77), 45, [&"armor"], &"knight", 1.0), 45, BH.Rarity.LEGENDARY, TestCase.rng(4401))
	var t2 := _float(Tips.item(sample, {"hero": hero, "compare": false}), Vector2(300, 60))
	var w := ItemGenerator.generate(DB.item_base(&"watchmans_halberd"), 45, BH.Rarity.LEGENDARY, TestCase.rng(4402))
	var t3 := _float(Tips.item(w, {"hero": hero, "compare": false}), Vector2(860, 60))
	await _shot("gear_04_new_legendary_armor_and_weapon")
	t2.queue_free()
	t3.queue_free()
	var mat := _float(Tips.item(iron, {"hero": hero}), Vector2(60, 80))
	await _shot("gear_05_material_tooltip_sources")
	mat.queue_free()

func _base(cat: StringName) -> StringName:
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category == cat and b.unique_name == "" and b.set_id == &"" and b.drop_weight > 0 and b.level_req <= 40 and b.level_req >= 25:
			return b.id
	return &""

func _hold(h: HeroData, f: Callable) -> void:
	h._checking_promotions = true
	f.call()
	h._checking_promotions = false

func _rank() -> void:
	var ui: UIRoot = Game.ui_root
	var h := Game.hero
	var tag := "touch" if Settings.touch_mode else "desktop"
	# a brand-new hero: unranked, the truthful first step
	h.rank_tracker = "expanded"
	Events.rank_tracker_changed.emit()
	await _shot("rank_%s_01_unranked_expanded" % tag)
	# a Class D hero working toward Class C
	_hold(h, func() -> void:
		h.progress.add_xp(XpCurve.total_xp_for_level(9))
		for f in [&"mq_maelis_orders", &"south_gate_open", &"mq_shard_taken", &"mq_three_told"]:
			h.world_flags[f] = true
		h.guild = &"swordfin"
		h.tier = 2
		h.equipment.tier_rank = 2
		h.guild_jobs["done"] = 2
		h.inventory.gold = 120)
	Events.rank_tracker_changed.emit()
	await _shot("rank_%s_02_expanded" % tag)
	h.rank_tracker = "minimized"
	Events.rank_tracker_changed.emit()
	await _shot("rank_%s_03_minimized" % tag)
	h.rank_tracker = "hidden"
	Events.rank_tracker_changed.emit()
	ui.open(&"character")
	await _shot("rank_%s_04_hidden_character_track_button" % tag)
	var cw := ui.window(&"character")
	cw._track_btn.pressed.emit()
	ui.close_all()
	await _shot("rank_%s_05_restored" % tag)
	# everything met: shown as ready (promotion fires on the next progress event)
	_hold(h, func() -> void:
		h.progress.add_xp(XpCurve.total_xp_for_level(12))
		h.world_flags[&"catacombs_ritual_seen"] = true
		h.guild_jobs["done"] = 5
		h.miniboss_log[&"greymaw"] = {"kills": 1, "at": 0.0}
		h.dungeon_raids["warren"] = {"at": 0.0, "until": 0.0, "count": 1}
		h.world_flags[DataDungeons.cleared_flag(&"warren")] = true
		h.inventory.gold = 500)
	Events.rank_tracker_changed.emit()
	await _shot("rank_%s_06_ready" % tag)
	notes["ready_guide"] = GuildRules.rank_guide(h).ready
	h.check_promotions()
	Events.rank_tracker_changed.emit()
	await _shot("rank_%s_07_promoted_next" % tag)
	notes["tier_after"] = h.tier

func _cam_zoom(z: float) -> void:
	var p := Game.player as Player
	var cam = p.get("camera_rig") if p else null
	if cam and "zoom" in cam:
		cam.zoom = z

func _creatures() -> void:
	var p := Game.player as Player
	p.hero.progress.add_xp(XpCurve.total_xp_for_level(30))
	Game.god_mode = true
	var ids := [&"gloomwraith", &"hive_drone", &"sporeling"]
	var spawned := []
	var origin := p.global_position
	for i in ids.size():
		var def := DB.enemy(ids[i])
		for k in 4:
			var at := origin + Vector3(-5.0 + 5.0 * i + (k % 2) * 1.6, 0, -4.0 - (k / 2) * 1.8)
			var e := Spawner.spawn_enemy(Game.current_map, def, 12, [], at, {})
			spawned.append(e)
	notes["models"] = {}
	for e in spawned:
		var en := e as Enemy
		notes.models[String(en.def.id)] = en.visual.appearance.get("model", "")
	await _wait(1.5)
	await _shot("creatures_01_group_far")
	# close looks: park the camera over each kind in turn
	for i in ids.size():
		var target: Enemy = spawned[i * 4]
		p.global_position = target.global_position + Vector3(0, 0, 3.2)
		await _wait(1.6)
		await _shot("creatures_02_close_%s" % ids[i])
	p.global_position = origin
	await _wait(2.5)
	await _shot("creatures_03_combat")
	notes["alive"] = spawned.filter(func(e): return is_instance_valid(e) and e.alive).size()

## The Malasugue route from the gameplay camera: the same hero positions before and after (--tag=before|after).
const ROUTE := [["01_south_gate", Vector3(0, 0, 34.5)], ["02_gate_road", Vector3(0, 0, 24.0)], ["03_plaza_south", Vector3(0, 0, 13.0)],
	["04_fountain_east", Vector3(6.5, 0, 5.5)], ["05_plaza_north_stair", Vector3(0, 0, -5.0)], ["06_terrace", Vector3(0, 2.0, -21.5)],
	["07_market_north", Vector3(12.5, 0, 17.0)], ["08_smithy_forge", Vector3(18.0, 0, 23.5)], ["09_market_south", Vector3(14.5, 0, 28.0)]]

func _town() -> void:
	var p := Game.player as Player
	Game.god_mode = true
	var tag := String(args.get("tag", "before"))
	var mode := "touch" if Settings.touch_mode else "desktop"
	for r in ROUTE:
		var at: Vector3 = r[1]
		var q := PhysicsRayQueryParameters3D.create(Vector3(at.x, at.y + 20.0, at.z), Vector3(at.x, at.y - 20.0, at.z), BH.LAYER_WORLD)
		var hit := p.get_world_3d().direct_space_state.intersect_ray(q)
		var gy: float = (hit.position as Vector3).y if not hit.is_empty() else at.y
		p.global_position = Vector3(at.x, gy + 0.1, at.z)
		p.velocity = Vector3.ZERO
		await _wait(1.4)
		await _shot("town_%s_%s_%s" % [tag, mode, r[0]])
	notes["dressing_skipped"] = Game.current_map.get_meta(&"dressing_skipped", [])
	var fc: Vector3 = Game.current_map.get_meta(&"fish_corner", Vector3.ZERO)
	notes["fish_corner"] = [fc.x, fc.z]
	p.global_position = fc + Vector3(0, 0.3, 3.0)
	await _wait(1.4)
	await _shot("town_%s_%s_10_fishmonger_corner" % [tag, mode])
	notes["route"] = ROUTE.map(func(r): return [r[0], [r[1].x, r[1].y, r[1].z]])
	notes["tag"] = tag

func _tavern() -> void:
	var p := Game.player as Player
	var tag := String(args.get("tag", "before"))
	for r in [["01_door", Vector3(1.0, 0.1, 4.6)], ["02_room", Vector3(0.5, 0.1, 0.5)], ["03_bar", Vector3(4.0, 0.1, -1.2)], ["04_hearth", Vector3(-4.0, 0.1, 1.5)]]:
		p.global_position = r[1]
		p.velocity = Vector3.ZERO
		await _wait(1.3)
		await _shot("tavern_%s_%s" % [tag, r[0]])

func _boss() -> Enemy:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if (e as Enemy).is_boss:
			return e
	return null

func _attack(b: Enemy, id: StringName) -> void:
	for a in b.def.attacks:
		if a.id == id:
			b.cooldowns.erase(id)
			b.brain.go(EnemyBrain.State.CHASE)
			b._start_attack(a)
			return

func _warden() -> void:
	var p := Game.player as Player
	Game.god_mode = true
	await _wait(1.0)
	var b := _boss()
	notes["boss"] = String(b.def.id) if b else "none"
	if b == null:
		return
	var pil: Node3D = ArenaState.pillars(Game.current_map)[1]
	var to_boss := (b.global_position - pil.global_position).slide(Vector3.UP).normalized()
	p.global_position = pil.global_position + to_boss * 2.6
	b.alert_to(p.global_position)
	b.target = p
	await _wait(1.0)
	_attack(b, &"charge")
	notes["charge_started"] = {"attack": String(b.current_attack.get("id", "")), "charge": not b._charge.is_empty(), "state": b.brain.state,
		"boss_to_pillar": b.global_position.distance_to(pil.global_position), "boss_to_player": b.global_position.distance_to(p.global_position)}
	await _wait(0.7)
	await _shot("warden_01_anticipation_charge_line")
	p.global_position += to_boss.cross(Vector3.UP) * 3.5           # sidestep the line
	for i in 40:
		await _wait(0.1)
		if b.status.has(&"stunned"):
			break
	await _wait(0.4)
	await _shot("warden_02_response_pillar_breaks_stun")
	notes["pillars_left_after_bait"] = ArenaState.intact_count(Game.current_map)
	b.hp = b.max_hp() * 0.3
	b._boss_phase_check()
	await _wait(1.6)
	await _shot("warden_03_later_phase_guidance")
	b.status.remove(&"stunned")
	b.status.remove(&"stun_immune")
	p.global_position = b.global_position + Vector3(0, 0, 14)
	b.target = p
	await _wait(0.6)
	_attack(b, &"charge")
	await _wait(2.4)
	await _shot("warden_04_phase3_charge_trail")
	Game.god_mode = false
	p.die(b)
	await _wait(3.0)
	await _shot("warden_05_wipe_explains")

func _verdigast() -> void:
	var p := Game.player as Player
	Game.god_mode = true
	await _wait(1.0)
	var b := _boss()
	notes["boss"] = String(b.def.id) if b else "none"
	if b == null:
		return
	p.global_position = b.global_position + Vector3(0, 0, 9)
	b.alert_to(p.global_position)
	b.target = p
	await _wait(1.0)
	_attack(b, &"bud")
	await _wait(2.2)
	await _shot("verdigast_01_buds_and_warnings")
	var buds := get_tree().get_nodes_in_group(&"rot_bud")
	if buds.size() > 0:
		(buds[0] as Enemy).die(p)
	await _wait(1.0)
	await _shot("verdigast_02_bud_broken_ground_saved")
	await _wait(8.0)
	await _shot("verdigast_03_unbroken_bud_bloomed_rot")
	notes["rot_patches"] = get_tree().get_nodes_in_group(&"rot_patch").size()
	b.hp = b.max_hp() * 0.6
	b._boss_phase_check()
	await _wait(1.5)
	_attack(b, &"bud")
	await _wait(1.6)
	_attack(b, &"spore_nova")
	await _wait(0.9)
	await _shot("verdigast_04_phase2_ring_and_buds")
	Game.god_mode = false
	p.die(b)
	await _wait(3.0)
	await _shot("verdigast_05_wipe_explains")
