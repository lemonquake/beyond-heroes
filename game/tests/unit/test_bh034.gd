extends TestCase
## bh-034: the Ascendant tiers (Cosmic, Divine, Eternal, Primordial): catalogue, models, rolls, drops, gates, sets,
## saves and the worn look.

const TIERS := [BH.Rarity.COSMIC, BH.Rarity.DIVINE, BH.Rarity.ETERNAL, BH.Rarity.PRIMORDIAL]
const CATS := [&"weapon", &"shield", &"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots", &"accessory"]

func _init() -> void:
	strict = true

func test_rarity_tables_cover_every_tier() -> void:
	eq(BH.RARITY_COUNT, 15, "four tiers above Aether, and Eschaton (bh-041) above them")
	eq(BH.RARITY_NAMES.slice(10), ["Cosmic", "Divine", "Eternal", "Primordial", "Eschaton"], "tier names in order")
	for t in [BH.RARITY_NAMES, BH.RARITY_COLORS, BH.RARITY_DESC, BH.RARITY_BEAM, BH.RARITY_DROP_SOUND, ItemGenerator.RULES,
			ItemGenerator.WEIGHTS, ItemGenerator.MIN_ILVL, ItemGenerator.RARITY_BUDGET, ItemInstance.SELL_MULT, LootFx.SPARKLE_COUNT,
			LootFx.SPARKLE_SIZE, LootFx.SPARKLE_ALPHA, LootFx.GLOW_STRENGTH, LootFx.GLINT_STRENGTH, DataCrystals.MAX_SOCKETS,
			DataLapeLines.TIER]:
		eq((t as Array).size(), BH.RARITY_COUNT, "a per-rarity table has a row for every rarity")
	for r in TIERS:
		ok(UIArt.rarity_frame(r) != null and UIArt.rarity_glow(r) != null, "%s has its slot frame and glow" % BH.rarity_name(r))
		ok(AscendantFx.has_look(r), "%s has its moving light" % BH.rarity_name(r))
	done()

func test_ten_of_every_type_in_every_tier() -> void:
	var count := {}
	for b: ItemBaseDef in DB.item_bases.values():
		if DataAscendant.is_ascendant(b):
			var k := "%d/%s" % [b.fixed_rarity, b.category]
			count[k] = int(count.get(k, 0)) + 1
	for r in TIERS:
		for c in CATS:
			eq(int(count.get("%d/%s" % [r, c], 0)), 10, "%s %s pieces" % [BH.rarity_name(r), c])
	eq(DataAscendant.COLLECTIONS.size(), 40, "forty collections")
	done()

func test_every_piece_has_its_model_and_icon() -> void:
	for b: ItemBaseDef in DB.item_bases.values():
		if not DataAscendant.is_ascendant(b):
			continue
		ok(ResourceLoader.exists(b.model), "%s model" % b.id)
		ok(ResourceLoader.exists(b.icon), "%s icon" % b.id)
		ok(b.boss_exclusive and b.drop_weight == 0, "%s never enters ordinary loot" % b.id)
		if b.category in [&"gloves", &"boots"]:
			ok(ResourceLoader.exists(b.model.get_basename() + "_R.glb"), "%s has its right-side model" % b.id)
	done()

func test_rolls_are_ascendant_and_stronger() -> void:
	var r := rng(7)
	for row in DataAscendant.COLLECTIONS:
		for piece in DataAscendant.PIECES:
			var it := DB.make_item(DataAscendant.piece_id(StringName(row[0]), piece), BH.Rarity.COMMON, 110, r.randi())
			eq(it.rarity, int(row[1]), "%s keeps its tier" % it.base.id)
			ok(it.affixes.size() >= 4, "%s carries many enchantments (%d)" % [it.base.id, it.affixes.size()])
			ok(it.powers.has(String(DataAscendant.TIER[it.rarity].power)), "%s carries its tier's signature power" % it.base.id)
			ok(it.set_def() != null, "%s belongs to its collection's set" % it.base.id)
			var plain := ItemInstance.from_dict(it.to_dict())
			eq(plain.rarity, it.rarity, "the tier survives a save")
			if it.base.is_weapon():
				var aether := plain
				aether.rarity = BH.Rarity.AETHER
				ok(it.damage_range().x > aether.damage_range().x, "%s hits harder than the same roll at Aether" % it.base.id)
	done()

func test_ordinary_loot_never_ascends() -> void:
	var r := rng(3)
	for i in 20000:
		ok(ItemGenerator.roll_rarity(r, 3.0, 2.5, 300) <= BH.Rarity.AETHER, "a normal rarity roll stops at Aether")
	var sword: ItemBaseDef = DB.item_bases.values().filter(func(b): return b.is_weapon() and b.unique_name == "" and b.set_id == &"" and b.drop_weight > 0)[0]
	eq(ItemGenerator.generate(sword, 120, BH.Rarity.PRIMORDIAL, rng(1)).rarity, BH.Rarity.AETHER, "a plain base forced to Primordial is Aether")
	done()

func test_drops_only_from_dungeon_lords_of_level_70() -> void:
	var r := rng(11)
	for i in 500:
		ok(DataAscendant.roll_drop(69, true, &"knight", 2.0, r) == null, "below level 70 nothing drops")
		ok(DataAscendant.roll_drop(120, false, &"knight", 2.0, r) == null, "a boss outside a dungeon drops nothing")
	var by_tier := {}
	var own_class := 0
	var n := 0
	for i in 40000:
		var it := DataAscendant.roll_drop(120, true, &"mage", 0.0, r)
		if it == null:
			continue
		n += 1
		by_tier[it.rarity] = int(by_tier.get(it.rarity, 0)) + 1
		if it.base.class_hint == &"mage" or it.base.category == &"accessory":
			own_class += 1
		ok(it.base.category != &"shield", "a mage is never given a shield")
		ok(not it.base.is_weapon() or it.base.class_hint == &"mage", "a weapon drop is the hero's own class")
	near(float(n) / 40000.0, 0.087, 0.012, "about one level-120 dungeon lord in eleven leaves a piece")
	ok(int(by_tier.get(BH.Rarity.COSMIC, 0)) > int(by_tier.get(BH.Rarity.DIVINE, 0)), "Cosmic is the commonest")
	ok(int(by_tier.get(BH.Rarity.DIVINE, 0)) > int(by_tier.get(BH.Rarity.ETERNAL, 0)), "Divine before Eternal")
	ok(int(by_tier.get(BH.Rarity.ETERNAL, 0)) > int(by_tier.get(BH.Rarity.PRIMORDIAL, 0)), "Primordial is the rarest")
	ok(int(by_tier.get(BH.Rarity.PRIMORDIAL, 0)) > 0, "Primordial still happens")
	ok(float(own_class) / float(maxi(n, 1)) > 0.6, "most pieces suit the hero's class")
	for i in 400:
		var low := DataAscendant.roll_drop(75, true, &"knight", 0.0, r)
		ok(low == null or low.rarity == BH.Rarity.COSMIC, "a level-75 lord can only leave Cosmic")
	var forced := DataAscendant.roll_drop(5, false, &"ranger", 0.0, r, BH.Rarity.ETERNAL)
	ok(forced != null and forced.rarity == BH.Rarity.ETERNAL, "the debug floor forces a tier from any boss")
	done()

func test_guild_ranks_gate_the_tiers() -> void:
	eq(DataGuilds.rank_for_rarity(BH.Rarity.AETHER), 5, "Aether stays Class A")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.COSMIC), 6, "Cosmic needs Class S")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.DIVINE), 7, "Divine needs Class SS")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.ETERNAL), 8, "Eternal needs Class SSS")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.PRIMORDIAL), 8, "Primordial needs Class SSS")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.COMMON), 0, "Common needs no rank")
	done()

func test_sets_and_signature_powers() -> void:
	for row in DataAscendant.COLLECTIONS:
		var s := DB.item_set(StringName(row[0]))
		ok(s != null and s.pieces.size() == 9, "%s is a nine-piece set" % row[0])
		eq(s.thresholds(), [2, 4, 6], "%s bonuses at 2, 4 and 6 pieces" % row[0])
	for r in TIERS:
		var p := DB.power(StringName(DataAscendant.TIER[r].power))
		ok(p != null and p.tier == &"ascendant", "%s signature power is defined and never rolled at random" % BH.rarity_name(r))
		var f: StringName = DataAscendant.TIER[r].flag
		ok(DataAscendant.proc_chance(f, 1.0) > 0.0 and DataAscendant.proc_chance(f, 3.0) > DataAscendant.proc_chance(f, 1.0), "more pieces, more often")
		ok(DataAscendant.proc_chance(f, 99.0) <= 0.45 and DataAscendant.proc_power(f, 99.0) <= 2.2, "the signature power is capped")
	done()

func test_worn_pieces_ride_the_bones_with_their_light() -> void:
	var v := CharacterVisual.new()
	host.add_child(v)
	var cls := DB.class_def(&"knight")
	v.setup(cls.model_path, 1.0, cls.tint, &"knight")
	var eqp := Equipment.new()
	var col := &"worldforger"
	for pair in [[&"helm", "helm"], [&"armor", "armor"], [&"inner_garment", "inner"], [&"leggings", "leggings"], [&"gloves_1", "gloves"],
			[&"gloves_2", "gloves"], [&"boots_1", "boots"], [&"boots_2", "boots"], [&"accessory_1", "accessory"]]:
		eqp.slots[pair[0]] = DB.make_item(DataAscendant.piece_id(col, pair[1]), BH.Rarity.COMMON, 110, 1)
	v.dress_equipment(eqp)
	eq(v._set_nodes.filter(func(n): return String(n.name).begins_with("Set_")).size(), 9, "every Ascendant piece is worn")
	var lit := 0
	for node in v._set_nodes:
		for mi in (node as Node).find_children("*", "MeshInstance3D", true, false):
			for i in (mi as MeshInstance3D).mesh.get_surface_count():
				var m := (mi as MeshInstance3D).get_active_material(i)
				if m and m.next_pass is ShaderMaterial:
					lit += 1
	ok(lit > 0, "the tier's moving light lies over the worn pieces")
	ok(v._set_nodes.any(func(n): return (n as Node).find_child("AscendantAura", true, false) != null), "worn pieces shed the tier's motes")
	v.free()
	done()
