extends TestCase
## bh-022: crystal-infused names and socket art, waypoints at every safe haven, the Mythic / Eternal renowned Tempos,
## and the rebuilt boss collections (fitted GLBs, per-bone parts, textured palettes).

func _init() -> void:
	strict = true

func _gems(pairs: Array) -> Array:
	var out: Array = []
	for p in pairs:
		out.append(String(DataCrystals.id_of(p[0], p[1])))
	return out

func test_every_crystal_combination_has_a_name() -> void:
	var fams: Array = DataCrystals.ORDER
	# singles: four tiers each, rising with power
	for f in fams:
		eq(CrystalNames.suffix_for(_gems([[f, 0]])), CrystalNames.SINGLE[f][0], "%s fragment names tier 0" % f)
		eq(CrystalNames.suffix_for(_gems([[f, 3], [f, 3]])), CrystalNames.SINGLE[f][3], "%s two orbitals name tier 3" % f)
	# every pair has its own hybrid name, and names never repeat
	var seen := {}
	for i in fams.size():
		for j in range(i + 1, fams.size()):
			var nm := CrystalNames.hybrid_name(fams[i], fams[j])
			ok(nm != "", "%s + %s has a hybrid name" % [fams[i], fams[j]])
			ok(not seen.has(nm), "hybrid name %s is unique" % nm)
			seen[nm] = true
			eq(CrystalNames.hybrid_name(fams[j], fams[i]), nm, "pair order does not matter")
	eq(seen.size(), 66, "all 66 pairs named (bh-028: twelve families with the celestial orbs)")
	eq(CrystalNames.suffix_for(_gems([[&"nova", 0], [&"ember", 0]])), "of the Nova Blast", "Nova + Ember is the Nova Blast")
	eq(CrystalNames.suffix_for(_gems([[&"nova", 3], [&"ember", 3]])), "of the Eternal Nova Blast", "an Orbital pair is Eternal")
	eq(CrystalNames.suffix_for(_gems([[&"nova", 1], [&"ember", 1]])), "of the Grand Nova Blast", "a Shard pair is Grand")
	eq(CrystalNames.suffix_for(_gems([[&"nova", 1], [&"ember", 1], [&"vipera", 0]])), "of the Venomous Nova Blast",
		"a third family lends its epithet")
	# every subset of families (1..7 of them, the socket maximum), at every grade: a real suffix
	var count := 0
	var bad := 0
	for mask in range(1, 1 << fams.size()):
		var fs: Array = []
		for k in fams.size():
			if mask & (1 << k):
				fs.append(fams[k])
		if fs.size() > 7:
			continue
		for g in 4:
			var pairs: Array = []
			for f in fs:
				pairs.append([f, g])
			if not CrystalNames.suffix_for(_gems(pairs)).begins_with("of "):
				bad += 1
			count += 1
	eq(bad, 0, "every one of %d family/grade combinations is named" % count)
	eq(CrystalNames.suffix_for(["", ""]), "", "empty sockets give no name")
	done()

func test_display_names_carry_the_infusion() -> void:
	var it := DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 10, 7)
	var plain := it.display_name()
	it.sockets = 2
	it.gems = ["", ""]
	eq(it.display_name(), plain, "empty sockets keep the name")
	it.gems = [String(DataCrystals.id_of(&"nova", 1)), String(DataCrystals.id_of(&"ember", 0))]
	ok(it.display_name().ends_with("of the Nova Blast"), "socketed name: %s" % it.display_name())
	var boss := DB.make_item(&"boss_dragonforge_armor", BH.Rarity.MASTER, 30, 3)
	boss.sockets = 1
	boss.gems = [String(DataCrystals.id_of(&"ember", 2))]
	ok(boss.display_name().ends_with(" of the Blaze"), "set pieces take the suffix too: %s" % boss.display_name())
	var c := CrystalNames.color_for(it.gems)
	ok(c.a > 0.0 and c.r > 0.5, "the infusion colour blends the families")
	done()

func test_socket_art_exists_for_every_crystal() -> void:
	ok(UIArt.tex(SocketArt.EMPTY) != null, "empty socket sprite")
	for f in DataCrystals.ORDER:
		for g in 4:
			ok(SocketArt.socket_tex(String(DataCrystals.id_of(f, g))) != null, "socket sprite %s %d" % [f, g])
	var it := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 10, 7)
	it.sockets = 3
	it.gems = [String(DataCrystals.id_of(&"aqua", 3)), "", ""]
	var slot := ItemSlot.new()
	host.add_child(slot)
	slot.set_item(it)
	ok(slot.is_processing(), "a socketed piece's cell animates its infusion glow")
	slot.free()
	var strip := SocketArt.Strip.new(it, 30.0)
	ok(strip.custom_minimum_size.x >= 90.0, "the tooltip strip shows every socket")
	strip.free()
	done()

func test_every_safe_haven_has_a_waypoint() -> void:
	for id in [&"gate_shrine", &"mill_shrine"]:
		ok(DataIsland.NETWORK.has(id), "%s is a network waypoint" % id)
		ok(DataIsland.NETWORK_SHRINES.has(id), "%s can be travelled to" % id)
		ok(DataIsland.place(DataIsland.NETWORK[id].place).get("shrine", "") == String(id), "%s stands at its place" % id)
	for p in DataIsland.all_places():
		if String(p.get("levels", "")) != "Safe haven" or not p.has("pos"):
			continue
		var has_shrine := false
		for id in DataIsland.NETWORK:
			if DataIsland.NETWORK[id].map == StringName(p.map):
				has_shrine = true
		ok(has_shrine, "the safe haven %s has a waypoint on its map" % p.id)
	done()

func test_renowned_tiers_replace_and_grow() -> void:
	eq(DataTempos.renowned_tier_for(24), 0, "level 24: the Renowned")
	eq(DataTempos.renowned_tier_for(25), 1, "level 25: the Mythic")
	eq(DataTempos.renowned_tier_for(45), 2, "level 45: the Eternal")
	var prev_max := 0
	var prev_mirror := 0.0
	for tier in 3:
		var lvl := int(DataTempos.renowned_tier(tier).level)
		var ids := DataTempos.legend_ids(lvl)
		eq(ids.size(), 5, "five at the shrine in tier %d" % tier)
		var lo := 1 << 30
		var hi := 0
		for id in ids:
			var lg := DataTempos.legend(id)
			eq(DataTempos.legend_tier(id), tier, "%s belongs to tier %d" % [id, tier])
			ok(int(lg.level) >= lvl, "%s answers at level %d or more" % [id, lvl])
			lo = mini(lo, int(lg.price))
			hi = maxi(hi, int(lg.price))
			for sid in lg.skills:
				ok(not DataTempos.skill(sid).is_empty(), "skill %s of %s exists" % [sid, id])
			ok(tier == 0 or DataTempos.portrait_path("tempo_%s" % id) != "", "%s has a portrait" % id)
		ok(lo > prev_max, "tier %d costs more than the tier below (%d > %d)" % [tier, lo, prev_max])
		prev_max = hi
		var mirror := float(DataTempos.renowned_tier(tier).mirror)
		ok(mirror > prev_mirror, "tier %d carries more of the hero" % tier)
		prev_mirror = mirror
		eq(DataTempos.summon_legend_ids(lvl).size(), 10, "ten in the tier-%d summon pool" % tier)
		for id in DataTempos.summon_legend_ids(lvl):
			eq(DataTempos.legend_tier(id), tier, "the tier-%d summon pool holds only its own (%s)" % [tier, id])
	for sid in DataTempos.SKILLS:
		var sk := DataTempos.skill(sid)
		if sk.has("unique"):
			ok(not DataTempos.legend(sk.unique).is_empty(), "%s belongs to a real spirit" % sid)
	done()

func test_mythic_spirit_binds_and_outgrows_the_renowned() -> void:
	var hero := Game.new_hero(&"knight", "Tier Test")
	hero.progress.level = 25
	hero.inventory.gold = 1000000
	hero.tempos.clear()
	var t := TempoRules.hire_legend(hero, &"branthor")
	ok(t != null, "a level-25 hero binds Branthor")
	if t:
		eq(t.grade_name(), "Mythic", "shown as Mythic")
		ok(t.mirror() > TempoRules.legend_data(&"hollan").mirror(), "a Mythic carries more of the hero than a Renowned")
	eq(hero.inventory.gold, 1000000 - 45000, "and costs its price")
	ok(TempoGacha.featured(3, 25) in DataTempos.summon_legend_ids(25), "the banner features a Mythic at level 25")
	ok(TempoRules.legend_data(&"hollan").mirror() == 0.75, "a Renowned already bound keeps its strength")
	done()

func test_boss_collections_use_the_fitted_models() -> void:
	for base in DataBossSets.bases():
		ok(ResourceLoader.exists(base.model_path()), "%s has a model" % base.id)
		ok(ResourceLoader.exists(base.icon_path()), "%s has an icon" % base.id)
	var v := CharacterVisual.new()
	host.add_child(v)
	var cls := DB.class_def(&"knight")
	v.setup(cls.model_path, 1.0, cls.tint, &"knight")
	var eqp := Equipment.new()
	for slot in DataBossSets.slots_for_set(&"crimson_glory"):
		if slot != &"main_weapon" and slot != &"sub_weapon":
			eqp.slots[slot] = DB.make_item(DataBossSets.piece_id(&"crimson_glory", slot), BH.Rarity.MASTER, 30, 1)
	v.dress_equipment(eqp)
	var bones := {}
	var textured := 0
	for n in v._set_nodes:
		bones[String(n.bone_name)] = true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			for i in mi.mesh.get_surface_count():
				var m := mi.get_surface_override_material(i) as StandardMaterial3D
				if m and m.albedo_texture != null:
					textured += 1
	for b in ["upper_arm.L", "upper_arm.R", "hand.L", "hand.R", "foot.L", "foot.R", "thigh.L", "thigh.R"]:
		ok(bones.has(b), "a worn part rides %s" % b)
	ok(textured > 10, "the collection wears the legend texture sets (%d textured surfaces)" % textured)
	v.free()
	done()
