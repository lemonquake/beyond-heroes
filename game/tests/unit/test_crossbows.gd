extends TestCase
## Equipment conservation, legacy save repair, crossbow combat and deterministic release timing.

func _init() -> void:
	strict = true

func _hero() -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(&"ranger"), "Weapon checks")
	h.progress.level = 60
	for attr in BH.ATTRIBUTES:
		h.progress.allocated[attr] = 100
	return h

func _item(id: StringName) -> ItemInstance:
	return DB.make_item(id, BH.Rarity.BEGINNER, 1, 721)

func _fill(h: HeroData) -> void:
	while h.inventory.free_cells() > 0:
		h.inventory.add(_item(&"iron_helm"))

func test_two_handed_shield_rejected_in_both_orders() -> void:
	for id in [&"hunters_bow", &"ashwood_crossbow"]:
		var e := Equipment.new()
		var bow := _item(id)
		var shield := _item(&"warden_kite_shield")
		ok(e.equip(shield, &"sub_weapon", 60, TempoRules.NO_ATTR).ok, "shield can be equipped first")
		var swap := e.equip(bow, &"main_weapon", 60, TempoRules.NO_ATTR)
		ok(swap.ok and swap.displaced.has(shield), "%s returns shield" % id)
		eq(e.get_item(&"sub_weapon"), null, "two-handed main clears sub")
		ok(not e.equip(shield, &"sub_weapon", 60, TempoRules.NO_ATTR).ok, "shield cannot be equipped after two-handed main")
		ok(not e.equip(_item(&"iron_longsword"), &"sub_weapon", 60, TempoRules.NO_ATTR).ok, "secondary weapon also rejected")
		ok(not e.equip(bow, &"sub_weapon", 60, TempoRules.NO_ATTR).ok, "two-handed item never fits sub hand")
		ok(not e.loadout().has_shield and not e.loadout().dual_wield, "combat loadout respects both hands")
	done()

func test_full_bag_swaps_conserve_items_for_player_and_tempo() -> void:
	for use_tempo in [false, true]:
		var h := _hero()
		var t := TempoData.new()
		t.class_id = &"swordsman"
		var e := t.equipment if use_tempo else h.equipment
		var sword := _item(&"iron_longsword")
		var shield := _item(&"warden_kite_shield")
		e.equip(sword, &"main_weapon", 60, TempoRules.NO_ATTR)
		e.equip(shield, &"sub_weapon", 60, TempoRules.NO_ATTR)
		# Swordsman supports greatswords; exercise the same two-hand displacement path as bows.
		var replacement := _item(&"rusted_claymore") if use_tempo else _item(&"ashwood_crossbow")
		ok(replacement != null, "replacement exists")
		h.inventory.add(replacement)
		_fill(h)
		var before := h.inventory.to_array()
		var error := TempoRules.equip_from_inventory(h, t, replacement, &"main_weapon") if use_tempo else h.equip_from_inventory(replacement, &"main_weapon")
		ok(error != "", "full bag prevents two displaced pieces")
		eq(h.inventory.to_array(), before, "failed swap leaves bag untouched")
		eq(e.get_item(&"main_weapon"), sword, "failed swap keeps main")
		eq(e.get_item(&"sub_weapon"), shield, "failed swap keeps shield")
		h.inventory.take(1)
		error = TempoRules.equip_from_inventory(h, t, replacement, &"main_weapon") if use_tempo else h.equip_from_inventory(replacement, &"main_weapon")
		eq(error, "", "one extra free cell allows the swap")
		ok(h.inventory.index_of(sword) >= 0 and h.inventory.index_of(shield) >= 0, "both displaced items preserved")
		eq(e.get_item(&"sub_weapon"), null, "sub hand cleared")
	done()

func test_drag_swap_cannot_put_bow_in_sub_hand() -> void:
	var h := _hero()
	var bow := _item(&"hunters_bow")
	h.equipment.equip(bow, &"main_weapon", 60, TempoRules.NO_ATTR)
	ok(h.swap_equipped(&"main_weapon", &"sub_weapon") != "", "drag swap rejected")
	eq(h.equipment.get_item(&"main_weapon"), bow, "main preserved")
	eq(h.equipment.get_item(&"sub_weapon"), null, "sub remains empty")
	done()

func test_legacy_save_keeps_invalid_offhand_until_bag_has_room() -> void:
	var h := _hero()
	_fill(h)
	h.equipment.slots[&"main_weapon"] = _item(&"hunters_bow")
	h.equipment.slots[&"sub_weapon"] = _item(&"warden_kite_shield")
	var t := TempoData.new()
	t.class_id = &"archer"
	t.equipment.slots[&"main_weapon"] = _item(&"ashwood_crossbow")
	t.equipment.slots[&"sub_weapon"] = _item(&"iron_longsword")
	h.tempos.append(t)
	var loaded := HeroData.from_dict(h.to_dict())
	eq(loaded.equipment.get_item(&"sub_weapon"), null, "legacy player shield no longer equipped")
	eq(loaded.tempos[0].equipment.get_item(&"sub_weapon"), null, "legacy Tempo secondary no longer equipped")
	eq(loaded.equipment.recovered_items.size(), 1, "full bag preserves shield in recovery")
	loaded = HeroData.from_dict(loaded.to_dict())
	eq(loaded.equipment.recovered_items.size(), 1, "pending recovery survives save/load")
	loaded.inventory.take(0)
	eq(loaded.inventory.count_of(&"warden_kite_shield"), 1, "freed slot automatically receives shield")
	eq(loaded.equipment.recovered_items.size(), 0, "shield delivered once")
	loaded.inventory.take(1)
	eq(loaded.inventory.count_of(&"iron_longsword"), 1, "Tempo displaced sword also recovered")
	loaded = HeroData.from_dict(loaded.to_dict())
	eq(loaded.inventory.count_of(&"warden_kite_shield"), 1, "no recovery duplicate on reload")
	done()

func test_crossbow_contract_and_release_over_10000_steps() -> void:
	var w := DB.weapon_type(&"crossbow")
	ok(w != null and w.ranged and w.two_handed and not w.dual_wieldable, "crossbow is two-handed ranged")
	ok(w.projectile_speed > DB.weapon_type(&"bow").projectile_speed, "faster bolts than arrows")
	ok(w.attacks_per_second < DB.weapon_type(&"bow").attacks_per_second, "reload trades speed for impact")
	ok(DataTempos.tempo_class(&"archer").weapons.has(&"crossbow"), "Archer Tempo can use crossbows")
	ok(DB.class_def(&"ranger").weapon_mastery.has(&"crossbow"), "Ranger mastery included")
	var t := TempoData.new()
	t.class_id = &"archer"
	var h := _hero()
	var crossbow := _item(&"ashwood_crossbow")
	h.inventory.add(crossbow)
	eq(TempoRules.equip_from_inventory(h, t, crossbow), "", "Archer Tempo can equip actual crossbow")
	var action: TimedAction
	var cycles := 0
	var shots := [0]
	for step in 10000:
		if action == null or action.finished:
			if action != null:
				eq(shots[0], cycles, "exactly one bolt per completed action")
			cycles += 1
			action = TimedAction.from_anim(w.light_anims[step % 4], 1.0)
			action.on_release = func(): shots[0] += 1
		action.step(1.0 / 60.0)
		ok(is_finite(action.elapsed) and action.elapsed <= action.duration + 1.0 / 60.0 + 0.0001, "finite bounded fixed-step action")
	ok(cycles > 150 and shots[0] >= cycles - 1, "sustained reload and fire cycles")
	done()

func test_crossbow_clips_exist_on_real_character() -> void:
	var visual := CharacterVisual.new()
	host.add_child(visual)
	visual.setup("res://assets/characters/ranger.glb", 1.0, Color.WHITE, &"ranger")
	for clip in [&"idle_crossbow", &"crossbow_aim", &"crossbow_fire", &"crossbow_heavy"]:
		ok(visual.has_anim(clip), "runtime rig contains %s" % clip)
	visual.free()
	done()

func test_player_basic_charged_and_skill_attacks_release_bolts() -> void:
	var previous_fx := FX.world
	var world := Node3D.new()
	host.add_child(world)
	FX.world = world
	var player := Player.new()
	world.add_child(player)
	var h := _hero()
	h.equipment.equip(_item(&"ashwood_crossbow"), &"main_weapon", 60, TempoRules.NO_ATTR)
	h.skill_tree.ranks[&"power_shot"] = 1
	player.bind(h)
	player.set_physics_process(false)
	player.aim_point = Vector3(0, 1.2, 12)
	eq(player.skill_block_reason(&"power_shot"), "", "Ranger shot can be used with crossbow")
	for mode in ["basic", "charged", "skill"]:
		if mode == "basic":
			player._start_light()
		elif mode == "charged":
			player._start_heavy(1.0, true)
		else:
			player._start_skill(&"power_shot")
		var a := player.action
		ok(a != null and a.release_t > 0.0, "%s has timed projectile release" % mode)
		ok(String(a.anim).begins_with("crossbow_"), "%s uses crossbow clip" % mode)
		a.step(a.release_t + 0.001)
		var projectiles := world.get_children().filter(func(node): return node is Projectile)
		eq(projectiles.size(), 1, "%s releases exactly one bolt" % mode)
		if not projectiles.is_empty():
			var bolt: Projectile = projectiles[0]
			eq(bolt.projectile_look, "bolt", "%s uses short bolt model" % mode)
			ok(bolt.request.use_weapon and bolt.velocity.is_finite(), "%s projectile carries weapon damage" % mode)
			if mode == "charged":
				eq(bolt.pierce, 2, "charged shot pierces two additional targets")
			bolt.free()
		player._cancel_action(true)
	world.queue_free()
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	FX.world = previous_fx if is_instance_valid(previous_fx) else null
	done()

func test_500_fast_bolts_do_not_tunnel_through_thin_wall() -> void:
	var world := Node3D.new()
	host.add_child(world)
	var wall := StaticBody3D.new()
	wall.collision_layer = BH.LAYER_WORLD
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(20, 20, 0.02)
	shape.shape = box
	wall.add_child(shape)
	world.add_child(wall)
	wall.position = Vector3(0, 3, 0.5)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	var bolts: Array[Projectile] = []
	var stopped := [0]
	for i in 500:
		var bolt := Projectile.spawn(world, Vector3(float(i % 20) * 0.1, 1.0 + float(i / 20) * 0.05, 0), Vector3.BACK, 1000.0, null, null, BH.LAYER_ENEMY, Elements.PHYSICAL, "bolt")
		bolt.set_physics_process(false)
		bolt.expired.connect(func(_point, hit_wall):
			if hit_wall:
				stopped[0] += 1)
		bolts.append(bolt)
	for bolt in bolts:
		bolt._physics_process(1.0 / 60.0)
		ok(bolt._done and bolt.global_position.is_finite(), "fast bolt ends at the wall with finite position")
	eq(stopped[0], 500, "all 500 concurrent swept bolts hit the 2 cm wall")
	await host.get_tree().physics_frame
	world.queue_free()
	await host.get_tree().physics_frame
	done()
