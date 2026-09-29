extends TestCase

func test_catalog_survives_saves_and_enters_level_gated_loot() -> void:
	var counts := {}
	var ids := {}
	for row in DataArtisanWeapons.ROWS:
		var b := DB.item_base(StringName(row[0]))
		ok(b != null and not ids.has(b.id), "new weapon is registered once")
		ids[b.id] = true
		counts[b.weapon_type] = int(counts.get(b.weapon_type, 0)) + 1
		ok(ResourceLoader.exists(b.model) and ResourceLoader.exists(b.icon), "%s has its own model and icon" % b.id)
		var model := ItemModels.instance(b)
		var bounds := ItemModels.bounds(model)
		ok(bounds.size.length() > 0.25 and bounds.size.length() < 2.5, "%s is an actual weapon-sized mesh" % b.id)
		model.free()
		var item := ItemGenerator.generate(b, b.level_req, BH.Rarity.ADVANCED, rng(283))
		eq(ItemInstance.from_dict(item.to_dict()).base.id, b.id, "item identity survives a save roundtrip")
		var excluded := DB.item_bases.keys().filter(func(id): return id != b.id)
		var drop := ItemGenerator.random_base(rng(191), b.drop_level, [&"weapon"], b.class_hint, 1.0, excluded)
		eq(drop.id, b.id, "%s is eligible for normal loot at its own level" % b.id)
		ok(b.drop_level == b.level_req and b.drop_weight > 0, "new weapon uses normal level gating")
	for family in [&"bow", &"crossbow", &"dagger", &"sword", &"axe"]:
		eq(counts.get(family, 0), 10, "ten designs per requested family")
	done()
