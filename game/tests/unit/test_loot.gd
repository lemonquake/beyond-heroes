extends TestCase
## bh-006: item weight and carry capacity, the weapon roster (own attack rate + weight), 3D item models and icons, the
## twenty new consumables, drop landing / pickup (the "cannot pick it up" bug), auto-loot and the Town Portal.

const NEW_TYPES := [&"sword", &"axe", &"greataxe", &"spear", &"javelin", &"club", &"dagger", &"claw", &"knuckles", &"bow"]

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _begin(map_id: StringName, spawn: StringName = &"start") -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "auto": Settings.auto_loot_enabled,
		"mode": Settings.auto_loot_mode}
	_holder = Node3D.new()
	_holder.name = "LootTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Looter")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, spawn)
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	Settings.auto_loot_enabled = _saved.auto
	Settings.auto_loot_mode = _saved.mode
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

# ---- weight ------------------------------------------------------------------------------------------------------

func test_every_item_has_weight_and_equipment_is_heavy() -> void:
	var equip: Array[float] = []
	var other: Array[float] = []
	for b: ItemBaseDef in DB.item_bases.values():
		ok(b.weight > 0.0, "%s has a weight" % b.id)
		if BH.CATEGORY_SLOTS.has(b.category):
			equip.append(b.weight)
		else:
			other.append(b.weight)
	other.sort()
	var median := other[other.size() / 2]
	var mean_e := 0.0
	for w in equip:
		mean_e += w
	mean_e /= equip.size()
	var mean_o := 0.0
	for w in other:
		mean_o += w
	mean_o /= other.size()
	for w in equip:
		ok(w >= median * 4.0, "equipment weight %.2f is at least 4x a typical item (%.2f)" % [w, median])
	ok(mean_e >= mean_o * 10.0, "equipment averages 10x the weight of other items (%.2f vs %.2f)" % [mean_e, mean_o])
	done()

func test_boots_raise_move_speed() -> void:
	var n := 0
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category != &"boots":
			continue
		n += 1
		var ms := 0.0
		for m in b.implicit:
			if m.stat == &"move_speed" and m.op == StatModifier.Op.INC:
				ms += m.value
		ok(ms > 0.0, "%s grants movement speed" % b.id)
	ok(n >= 6, "six boots bases")
	var h := Game.new_hero(&"knight", "Boots")
	var before := h.compute_stats().get_stat(&"move_speed")
	var boot := DB.make_item(&"soft_boot", BH.Rarity.COMMON, 1, 3)
	h.inventory.add(boot)
	var mid := h.compute_stats().get_stat(&"move_speed")   # carried in the bag: a little heavier
	eq(h.equip_from_inventory(boot, &"boots_1"), "", "boots equip")
	ok(h.compute_stats().get_stat(&"move_speed") > mid, "wearing boots is faster than carrying them")
	ok(h.compute_stats().get_stat(&"move_speed") > before, "and faster than without them")
	done()

func test_strength_carry_and_speed() -> void:
	var h := Game.new_hero(&"knight", "Strong")
	var cls := h.cls
	var attrs := h.progress.base_attributes()
	var s0 := StatCalculator.compute(cls, 1, attrs, [], WeaponLoadout.new())
	var a2 := attrs.duplicate()
	a2[&"str"] = int(a2[&"str"]) + 30
	var s1 := StatCalculator.compute(cls, 1, a2, [], WeaponLoadout.new())
	near(s1.get_stat(&"carry_capacity") - s0.get_stat(&"carry_capacity"), 30.0 * StatCalculator.CARRY_PER_STR, 0.001, "+30 STR adds carry capacity")
	ok(s1.get_stat(&"move_speed") > s0.get_stat(&"move_speed"), "Strength raises movement speed")
	done()

func test_load_slows_and_overburdens() -> void:
	var h := Game.new_hero(&"knight", "Mule")
	h.init_new()
	var light := h.compute_stats()
	ok(light.get_stat(&"load") > 0.0 and light.get_stat(&"load") < 1.0, "starting gear is a partial load (%.2f)" % light.get_stat(&"load"))
	ok(not light.has_flag(&"overburdened"), "not overburdened at the start")
	var cap := light.get_stat(&"carry_capacity")
	# fill the bag with plate until the load passes 100%
	while h.compute_stats().get_stat(&"load") < 1.02:
		h.inventory.add(DB.make_item(&"warden_plate", BH.Rarity.COMMON, 20, h.inventory.free_cells()))
		if h.inventory.free_cells() == 0:
			break
	var heavy := h.compute_stats()
	ok(heavy.get_stat(&"carry_weight") > cap, "carried weight exceeds capacity")
	ok(heavy.has_flag(&"overburdened"), "overburdened at 100%+ load")
	ok(heavy.get_stat(&"move_speed") < light.get_stat(&"move_speed") * 0.7, "overburdened is much slower")
	var prev := 2.0
	for i in 21:
		var m := StatCalculator.load_move_mult(i * 0.05)
		ok(m <= prev + 0.00001, "load slowdown is monotonic at %d%%" % (i * 5))
		prev = m
	eq(StatCalculator.load_move_mult(StatCalculator.LOAD_FREE), 1.0, "no slowdown up to the free load")
	done()

# ---- weapons -----------------------------------------------------------------------------------------------------

func test_weapon_roster() -> void:
	for t in NEW_TYPES:
		var wt := DB.weapon_type(t)
		ok(wt != null, "weapon type %s exists" % t)
		if wt == null:
			continue
		for a in wt.light_anims + [wt.heavy_anim]:
			ok(not DB.anim(a).is_empty(), "%s uses an existing clip %s" % [t, a])
		var seen := {}
		var n := 0
		for b: ItemBaseDef in DB.item_bases.values():
			if b.is_weapon() and b.weapon_type == t and b.unique_name == "":
				n += 1
				ok(b.attacks_per_second > 0.0, "%s has its own attack speed" % b.id)
				var key := "%.2f/%.2f" % [b.attacks_per_second, b.weight]
				ok(not seen.has(key), "%s: attack speed + weight differ from %s" % [b.id, seen.get(key, "")])
				seen[key] = b.id
		ok(n >= 5, "%s has at least five weapons (%d)" % [t, n])
	eq(DB.weapon_type(&"greataxe").two_handed, true, "great axes are two-handed")
	eq(DB.weapon_type(&"axe").two_handed, false, "axes are one-handed")
	done()

func test_weapon_attack_rate_comes_from_the_item() -> void:
	var h := Game.new_hero(&"knight", "Rate")
	h.progress.add_xp(XpCurve.total_xp_for_level(40))
	for a in BH.ATTRIBUTES:
		h.progress.allocated[a] = 60
	for id in [&"brass_knuckles", &"executioner_moon", &"reed_javelin", &"duelist_sabre"]:
		var it := DB.make_item(id, BH.Rarity.COMMON, 40, 1)
		h.inventory.add(it)
		eq(h.equip_from_inventory(it, &"main_weapon"), "", "equip %s" % id)
		var d := h.compute_stats()
		near(d.loadout.aps(), it.base.attacks_per_second, 0.0001, "%s loadout rate" % id)
		near(d.get_stat(&"attacks_per_second"), it.base.attacks_per_second * d.get_stat(&"attack_speed"), 0.0001, "%s attacks/s" % id)
	# dual wield averages both hands
	var a := DB.make_item(&"iron_talons", BH.Rarity.COMMON, 40, 2)
	var b := DB.make_item(&"tiger_claw", BH.Rarity.COMMON, 40, 3)
	h.inventory.add(a)
	h.inventory.add(b)
	h.equip_from_inventory(a, &"main_weapon")
	eq(h.equip_from_inventory(b, &"sub_weapon"), "", "claws dual wield")
	near(h.compute_stats().loadout.aps(), (a.base.attacks_per_second + b.base.attacks_per_second) * 0.5, 0.0001, "dual wield averages the two rates")
	done()

# ---- models and icons --------------------------------------------------------------------------------------------

func test_every_item_has_a_model_and_icon() -> void:
	for b: ItemBaseDef in DB.item_bases.values():
		ok(ResourceLoader.exists(ItemBaseDef.ITEM_MODEL % b.id), "%s has its own model" % b.id)
		ok(ResourceLoader.exists(b.icon_path()), "%s icon exists" % b.id)
		if b.icon.contains("items3d"):
			ok(ResourceLoader.exists(b.icon), "%s rendered icon exists" % b.id)
	ok(ResourceLoader.exists(ItemModels.GOLD_MODEL), "gold pile model")
	# a sample of ground presentations: meshes, resting on the ground, visible size
	for id in [&"iron_longsword", &"brass_knuckles", &"copper_ring", &"warden_plate", &"health_potion", &"town_portal", &"sigil_buckler"]:
		var g := ItemModels.ground_instance(DB.item_base(id))
		host.add_child(g)
		var meshes := g.find_children("*", "MeshInstance3D", true, false)
		ok(meshes.size() > 0, "%s model has meshes" % id)
		var bb := ItemModels.bounds(g)
		near(bb.position.y, 0.01, 0.02, "%s rests on the ground" % id)
		ok(maxf(bb.size.x, maxf(bb.size.y, bb.size.z)) >= ItemModels.GROUND_MIN_SIZE - 0.01, "%s is visible on the ground" % id)
		ok(bb.size.y < maxf(bb.size.x, bb.size.z) + 0.001 or DB.item_base(id).category in [&"consumable", &"helm", &"boots"], "%s lies flat" % id)
		g.free()
	done()

# ---- consumables ---------------------------------------------------------------------------------------------------

func test_twenty_new_consumables() -> void:
	var new_ids := []
	for b: ItemBaseDef in DB.item_bases.values():
		# bh-007's recipe scrolls also use rendered icons; they are counted in test_crafting
		if b.is_consumable() and b.icon.contains("items3d") and not b.consumable_effect.has("learn_recipe"):
			new_ids.append(b.id)
			ok(b.flavor != "", "%s explains itself" % b.id)
			ok(b.stack_max > 1, "%s stacks" % b.id)
	eq(new_ids.size(), 20, "twenty new consumables")
	ok(new_ids.has(&"town_portal"), "the Town Portal is one of them")
	for b: ItemBaseDef in DB.item_bases.values():
		var fx := b.consumable_effect
		if fx.has("buff"):
			ok(StatusRules.DEFS.has(StringName(fx.buff)), "%s buff %s is defined" % [b.id, fx.buff])
			ok(ResourceLoader.exists(StatusRules.icon_of(StringName(fx.buff))), "%s buff has an icon" % b.id)
	done()

func test_using_consumables() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	var inv := p.hero.inventory
	for id in [&"swiftfoot_tonic", &"ironskin_brew", &"berserker_draught", &"sages_infusion", &"emberward_potion", &"frostward_potion",
			&"stormward_potion", &"fortune_elixir", &"scholars_tea", &"featherweight_draught", &"whetstone", &"smoke_pellet"]:
		var it := DB.make_item(id, BH.Rarity.COMMON, 10, 1)
		inv.add(it)
		var sid := StringName(it.base.consumable_effect.buff)
		ok(p.consume_item(it), "%s can be used" % id)
		ok(p.status.has(sid), "%s applies %s" % [id, sid])
		eq(inv.count_of(id), 0, "%s is used up" % id)
	p.ensure_stats()
	ok(p.stats.get_stat(&"carry_capacity") > p.hero.compute_stats().get_stat(&"carry_capacity") + 59.0, "Featherweight adds capacity")
	# potions (minor / superior) restore, sharing the potion cooldown
	p.hp = p.max_hp() * 0.2
	p.potion_cd = 0.0
	var pot := DB.make_item(&"superior_health_potion", BH.Rarity.COMMON, 20, 1)
	inv.add(pot)
	ok(p.use_potion(&"heal"), "the potion belt drinks the strongest health draught")
	eq(inv.count_of(&"superior_health_potion"), 0, "superior draught used first")
	# thrown bombs
	for id in [&"firebomb", &"frost_flask"]:
		var b := DB.make_item(id, BH.Rarity.COMMON, 10, 1)
		inv.add(b)
		p.aim_override = p.global_position + Vector3(4, 0, 0)
		p._update_aim()
		ok(p.consume_item(b), "%s is thrown" % id)
		eq(inv.count_of(id), 0, "%s used up" % id)
	await host.get_tree().create_timer(1.0).timeout
	# the Phoenix Feather is not drunk: it saves the hero from a killing blow
	var f := DB.make_item(&"phoenix_feather", BH.Rarity.COMMON, 10, 1)
	inv.add(f)
	ok(not p.consume_item(f), "the feather cannot be drunk")
	p.die(null)
	ok(p.alive, "the feather revives the hero")
	near(p.hp, p.max_hp() * 0.5, 1.0, "at half HP")
	eq(inv.count_of(&"phoenix_feather"), 0, "the feather burns away")
	p.die(null)
	ok(not p.alive, "without a feather the hero falls")
	_end()
	done()

# ---- drops: landing and pickup ------------------------------------------------------------------------------------

func test_drops_land_within_reach() -> void:
	await _begin(&"ruined_forest")
	var world := _player.get_world_3d()
	var space := world.direct_space_state
	var base := _player.global_position
	# a tall pillar next to the "corpse": the old ground ray (6 m up) landed drops on top of such colliders
	var pillar := StaticBody3D.new()
	pillar.collision_layer = BH.LAYER_WORLD
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(1.0, 3.5, 1.0)
	cs.shape = bs
	pillar.add_child(cs)
	Game.current_map.add_child(pillar)
	var corpse := base + Vector3(2.0, 0, 0)
	pillar.global_position = corpse + Vector3(1.4, 1.75, 0)
	await host.get_tree().physics_frame
	var fails := 0
	for i in 24:
		var ang := TAU * float(i) / 24.0
		var land: Vector3 = Loot.landing_point(world, corpse, ang, 1.8)
		var flat := Vector2(land.x - corpse.x, land.z - corpse.z).length()
		if absf(land.y - corpse.y) > 1.0 or flat > 1.85:
			fails += 1
		var q := PhysicsRayQueryParameters3D.create(corpse + Vector3.UP * 0.7, land + Vector3.UP * 0.7, BH.LAYER_WORLD | BH.LAYER_PROPS)
		if not space.intersect_ray(q).is_empty():
			fails += 1
	eq(fails, 0, "every drop lands on walkable ground in the open, near the corpse")
	pillar.free()
	_end()
	done()

func test_pickup_with_interact_and_auto_loot() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	Settings.auto_loot_enabled = false
	var it := DB.make_item(&"iron_longsword", BH.Rarity.BASIC, 3, 7)
	var d: LootDrop = Loot.spawn_item(it, p.global_position + Vector3(0.6, 0, 0), 0.0, 0.8)
	await host.get_tree().create_timer(0.6).timeout
	ok(d.landed, "the drop has landed")
	ok(not is_instance_valid(d) or d.is_in_group(&"loot"), "still on the ground with auto-loot off")
	p.interact()
	ok(p.hero.inventory.index_of(it) >= 0, "R picks the drop up")
	ok(not is_instance_valid(d) or d.is_queued_for_deletion(), "the drop is removed")
	# auto-loot on: walking near a matching drop collects it by itself
	Settings.auto_loot_enabled = true
	Settings.auto_loot_mode = 0
	var it2 := DB.make_item(&"health_potion", BH.Rarity.COMMON, 3, 8)
	Loot.spawn_item(it2, p.global_position + Vector3(0.5, 0, 0.5), 0.0, 0.6)
	await host.get_tree().create_timer(1.2).timeout
	ok(p.hero.inventory.count_of(&"health_potion") >= 5, "auto-loot picked the potion up")
	# the filter: Elite and better ignores a Common item
	Settings.auto_loot_mode = 4
	var it3 := DB.make_item(&"iron_helm", BH.Rarity.COMMON, 3, 9)
	var d3: LootDrop = Loot.spawn_item(it3, p.global_position + Vector3(-0.5, 0, 0.3), 0.0, 0.6)
	await host.get_tree().create_timer(1.0).timeout
	ok(is_instance_valid(d3) and d3.is_in_group(&"loot"), "the rarity filter leaves a Common helm on the ground")
	_end()
	done()

# ---- Town Portal ----------------------------------------------------------------------------------------------------

func _portals() -> Array:
	return host.get_tree().get_nodes_in_group(&"town_portal")

func test_town_portal() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	var h := p.hero
	ok(TownPortal.open_for(p), "a portal opens in the wilds")
	eq(String(h.town_portal.get("map", "")), "ruined_forest", "the portal is recorded")
	eq(_portals().size(), 1, "one portal stands")
	var first := Vector3(h.town_portal.pos[0], h.town_portal.pos[1], h.town_portal.pos[2])
	p.global_position += Vector3(3, 0, 0)
	ok(TownPortal.open_for(p), "a second scroll")
	eq(_portals().size(), 1, "opening another replaces the first")
	ok(Vector3(h.town_portal.pos[0], h.town_portal.pos[1], h.town_portal.pos[2]).distance_to(first) > 1.0, "at the new spot")
	var h2 := HeroData.from_dict(h.to_dict())
	eq(h2.town_portal.get("map", ""), h.town_portal.map, "the portal survives saving")
	await host.get_tree().create_timer(1.4).timeout
	var tp: TownPortal = _portals()[0]
	ok(tp.can_interact(p), "the open vortex can be entered")
	# the town end
	Game.load_map(&"sanctuary", &"waypoint")
	await host.get_tree().physics_frame
	var ends := _portals().filter(func(n): return (n as TownPortal).is_return)
	eq(ends.size(), 1, "a return portal waits in Malasugue")
	ok(not TownPortal.open_for(p), "no portal can be opened in town")
	TownPortal.dispel("")
	ok(h.town_portal.is_empty(), "dispelled")
	eq(_portals().size(), 0, "both ends close")
	# death expires it
	Game.load_map(&"ruined_forest", &"start")
	await host.get_tree().physics_frame
	ok(TownPortal.open_for(p), "open again")
	p.die(null)
	ok(h.town_portal.is_empty(), "the portal expires when the hero dies")
	_end()
	done()

func test_auto_loot_settings() -> void:
	ok(Settings.KEYS.has("auto_loot_enabled"), "the auto-loot switch is saved")
	eq(Settings.AUTO_LOOT_NAMES.size(), 5, "five auto-loot filters")
	var saved := Settings.auto_loot_mode
	Settings.auto_loot_mode = 0
	eq(Settings.auto_loot_rarity, BH.Rarity.BEGINNER, "all items")
	Settings.auto_loot_mode = 4
	eq(Settings.auto_loot_rarity, BH.Rarity.ELITE, "elite and better")
	Settings.auto_loot_mode = saved
	done()

# ---- critic pass 2: portal placement, pickup priority, dodge at full load ---------------------------------------------

func _pillar(at: Vector3, size := Vector3(1.0, 3.5, 1.0)) -> StaticBody3D:
	var b := StaticBody3D.new()
	b.collision_layer = BH.LAYER_WORLD
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	b.add_child(cs)
	Game.current_map.add_child(b)
	b.global_position = at + Vector3.UP * size.y * 0.5
	return b

func _portal_query() -> PhysicsShapeQueryParameters3D:
	var shape := CylinderShape3D.new()
	shape.radius = TownPortal.CLEAR_RADIUS
	shape.height = TownPortal.CLEAR_HEIGHT
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.collision_mask = BH.LAYER_WORLD | BH.LAYER_PROPS
	return q

func test_portal_never_opens_inside_scenery() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	# walk to an open patch away from the waypoint (the glade east of it)
	p.global_position = CombatQuery.ground_at(p.get_world_3d(), p.global_position + Vector3(9.0, 0, 3.0))
	p.rotation.y = 0.0
	await host.get_tree().physics_frame
	var fwd := p.forward()
	var side := fwd.cross(Vector3.UP).normalized()
	# a pillar just beside the straight-ahead line (the old thin-ray check let it stand inside the vortex)
	var pil := _pillar(p.global_position + fwd * 2.8 + side * 0.8)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	ok(TownPortal.open_for(p), "a portal still opens next to the pillar")
	var h := p.hero
	var spot := Vector3(h.town_portal.pos[0], h.town_portal.pos[1], h.town_portal.pos[2])
	ok(TownPortal.is_clear(p.get_world_3d().direct_space_state, _portal_query(), spot), "nothing solid inside the vortex")
	ok(Vector2(spot.x - pil.global_position.x, spot.z - pil.global_position.z).length() > TownPortal.CLEAR_RADIUS + 0.5,
		"the portal stands clear of the pillar")
	TownPortal.dispel("")
	pil.free()
	# boxed in on every side: no room, the scroll is kept
	var walls := []
	for d in [Vector3(1.6, 0, 0), Vector3(-1.6, 0, 0), Vector3(0, 0, 1.6), Vector3(0, 0, -1.6)]:
		walls.append(_pillar(p.global_position + d, Vector3(0.6 if d.x != 0.0 else 4.0, 3.5, 0.6 if d.z != 0.0 else 4.0)))
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	var scroll := DB.make_item(&"town_portal", BH.Rarity.COMMON, 1, 1)
	p.hero.inventory.add(scroll)
	ok(not p.consume_item(scroll), "no portal in a cramped spot")
	eq(p.hero.inventory.count_of(&"town_portal"), 1, "the scroll is not used up")
	for w in walls:
		w.free()
	_end()
	done()

func test_return_portal_stands_on_its_terrace_spot() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	ok(TownPortal.open_for(p), "open in the forest")
	Game.load_map(&"sanctuary", &"waypoint")
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	var ends := host.get_tree().get_nodes_in_group(&"town_portal").filter(func(n): return (n as TownPortal).is_return)
	eq(ends.size(), 1, "the return portal")
	if ends.size() == 1:
		var tp: TownPortal = ends[0]
		var mk: Transform3D = Game.current_map.spawn_transform(TownPortal.TOWN_MARKER)
		near(tp.global_position.distance_to(mk.origin), 0.0, 0.01, "at the designed terrace spot")
		ok(TownPortal.is_clear(p.get_world_3d().direct_space_state, _portal_query(), tp.global_position), "nothing solid inside it")
		ok(not TownPortal._near_landmark(tp.global_position), "clear of the waypoint, doors and townsfolk")
	TownPortal.dispel("")
	_end()
	done()

func test_r_prefers_loot_over_a_nearer_door() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	p.global_position = CombatQuery.ground_at(p.get_world_3d(), p.global_position + Vector3(9.0, 0, 3.0))
	var door := DoorPortal.new().setup(&"sanctuary", &"start", "Test door")
	Game.current_map.add_child(door)
	door.global_position = p.global_position + Vector3(1.2, 0, 0)
	var it := DB.make_item(&"hand_axe", BH.Rarity.BASIC, 3, 5)
	var d: LootDrop = Loot.spawn_item(it, p.global_position + Vector3(-1.55, 0, 0), 0.0, 0.01)
	await host.get_tree().create_timer(0.6).timeout
	eq(p.find_interact_target(), d, "a drop 1.55 m away wins over a door 1.2 m away")
	p.interact()
	ok(p.hero.inventory.index_of(it) >= 0, "R picked the drop up, not the door")
	eq(Game.current_map_id, &"ruined_forest", "and did not walk through the door")
	door.free()
	_end()
	done()

func test_no_dodge_when_overburdened() -> void:
	await _begin(&"ruined_forest")
	var p := _player
	p.dodge_cd = 0.0
	p.ensure_stats()
	ok(p._can_start(&"dodge"), "a normal load can dodge")
	while not p.hero.compute_stats().has_flag(&"overburdened") and p.hero.inventory.free_cells() > 0:
		p.hero.inventory.add(DB.make_item(&"tower_shield", BH.Rarity.COMMON, 12, p.hero.inventory.free_cells()))
	p.ensure_stats()
	ok(p.is_overburdened(), "overburdened")
	ok(not p._can_start(&"dodge"), "no dodge roll or step at full load")
	p.hero.skill_tree.ranks[&"leap_slam"] = 1
	ok(p.skill_block_reason(&"leap_slam").begins_with("Overburdened") or p.skill_block_reason(&"leap_slam") == "Cooldown", "leap skills are blocked too")
	_end()
	done()
