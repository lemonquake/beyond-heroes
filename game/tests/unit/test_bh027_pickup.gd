extends TestCase
## bh-027: every drop a monster leaves can be picked up with R, and leaves the ground when it is.

var _saved := {}
var _holder: Node3D
var _player: Player

func _init() -> void:
	strict = true

func _begin(map_id: StringName, spawn: StringName = &"start") -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "auto": Settings.auto_loot_enabled}
	_holder = Node3D.new()
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Picker")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, spawn)
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	Settings.auto_loot_enabled = _saved.auto
	for t in TempoParty.actors(host.get_tree()):
		t.free()
	for n in host.get_tree().get_nodes_in_group(&"loot"):
		n.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

func _drops() -> Array:
	return host.get_tree().get_nodes_in_group(&"loot").filter(func(d): return is_instance_valid(d) and not d.is_queued_for_deletion() and (d as LootDrop).item != null)

func _collect_all(p: Player) -> Array:
	var stuck := []
	for pass_i in 6:
		var drops := _drops()
		if drops.is_empty():
			break
		for dd in drops:
			if not is_instance_valid(dd) or dd.is_queued_for_deletion():
				continue
			var d := dd as LootDrop
			if p.hero.inventory.free_cells() < 6:
				for c in p.hero.inventory.cells.size():
					p.hero.inventory.cells[c] = null
			p.global_position = d.global_position + Vector3(0.25, 0.05, 0)
			await host.get_tree().physics_frame
			if p.find_interact_target() == d:
				p.interact()
			await host.get_tree().process_frame
	for dd in _drops():
		var d := dd as LootDrop
		p.global_position = d.global_position + Vector3(0.25, 0.05, 0)
		await host.get_tree().physics_frame
		var tgt := p.find_interact_target()
		stuck.append("%s (%s) landed=%s can=%s dist=%.2f dy=%.2f pos=%s target=%s" % [d.item.display_name(), d.item.base.category,
			d.landed, d.can_interact(p), p.interact_distance(d), d.global_position.y - p.global_position.y, d.global_position,
			(tgt as LootDrop).item.display_name() if tgt is LootDrop else str(tgt)])
	return stuck

func test_every_boss_drop_can_be_picked_up() -> void:
	await _begin(&"ruined_forest")
	Settings.auto_loot_enabled = false
	var p := _player
	p.hero.progress.add_xp(XpCurve.total_xp_for_level(20))
	var r := rng(27)
	var start := p.global_position
	for k in 14:
		var at := CombatQuery.ground_at(p.get_world_3d(), start + Vector3(r.randf_range(-40, 40), 30.0, r.randf_range(-40, 40)))
		var boss := k % 2 == 0
		var e := Enemy.new().setup(DB.enemy(&"hollow_soldier"), 20, [] if boss else [&"shielded"])
		e.is_boss = boss
		e.is_elite = not boss
		Game.current_map.add_child(e)
		e.global_position = at
		p.global_position = at + Vector3(2, 0.1, 0)
		await host.get_tree().physics_frame
		Loot.drop_for(e, p)
		e.free()
	await host.get_tree().create_timer(0.8).timeout
	var n := _drops().size()
	ok(n >= 40, "a lot of loot on the ground (%d)" % n)
	var stuck: Array = await _collect_all(p)
	eq(stuck, [], "every drop was picked up and left the ground")
	_end()
	done()

func test_a_drop_from_the_air_falls_to_the_ground_and_can_be_taken() -> void:
	await _begin(&"ruined_forest")
	Settings.auto_loot_enabled = false
	var p := _player
	var ground := p.global_position
	# a monster killed 9 m up (a leap, a knock-up, a flyer): nothing walkable within the old 4 m search
	var it := DB.make_item(DataCrystals.id_of(&"ember", 0), BH.Rarity.COMMON, 5, 3)
	var d: LootDrop = Loot.spawn_item(it, ground + Vector3(1.0, 9.0, 0.0), 0.0, 0.5)
	await host.get_tree().create_timer(0.8).timeout
	ok(absf(d.global_position.y - ground.y) < 1.2, "the drop came down to the ground (%.2f m above the hero)" % (d.global_position.y - ground.y))
	p.global_position = d.global_position + Vector3(0.3, 0.05, 0)
	await host.get_tree().physics_frame
	p.interact()
	ok(not is_instance_valid(d) or d.is_queued_for_deletion(), "and R picks it up")
	# a hovered tag is forgotten when the tags are hidden: the next click is an attack again
	var d2: LootDrop = Loot.spawn_item(DB.make_item(&"hand_axe", BH.Rarity.BASIC, 3, 4), ground + Vector3(-3, 0, 0), 0.0, 0.2)
	await host.get_tree().create_timer(0.6).timeout
	var labels := LootLabels.new()
	host.add_child(labels)
	var always := Settings.loot_labels_always
	Settings.loot_labels_always = false
	Game.hover_loot = d2
	await host.get_tree().process_frame
	await host.get_tree().process_frame
	ok(Game.hover_loot == null, "no stale click target once the loot tags are hidden")
	Settings.loot_labels_always = always
	labels.free()
	_end()
	done()
