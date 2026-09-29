extends TestCase

func _init() -> void:
	strict = true

func test_class_bias_and_weapon_families() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		for level in [3, 15, 35, 60]:
			var r := rng(level * 91)
			var fits := 0
			var families := {}
			for i in 2500:
				var b := ItemGenerator.random_base(r, level, [], cls)
				if ItemGenerator.class_fit(b, cls):
					fits += 1
				if b.is_weapon():
					families[b.weapon_type] = int(families.get(b.weapon_type, 0)) + 1
			ok(fits >= 1950, "%s level %d: at least ~80%% class-related (%d/2500)" % [cls, level, fits])
			if cls == &"knight":
				ok(int(families.get(&"axe", 0)) >= 55, "axes appear regularly at level %d" % level)
				ok(int(families.get(&"greataxe", 0)) >= 55, "great axes appear regularly at level %d" % level)
	done()

func test_every_champion_equipment_piece_and_special_is_class_compatible() -> void:
	var saved_rng := Loot.rng.state
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var p := Player.new()
		p.hero = Game.new_hero(cls, "Loot QA")
		p.stats = p.hero.compute_stats()
		for level in [1, 8, 25, 60]:
			for boss in [false, true]:
				var e := Enemy.new().setup(DB.enemy(&"hollow_soldier"), level)
				e.is_boss = boss
				if not boss:
					e.miniboss = {"id": "loot_test"}
				for roll in 60:
					var items := Loot.equipment_for(e, p)
					ok(items.size() >= (5 if boss else 3), "champion always drops equipment")
					ok(items[0].base.is_weapon(), "champion always drops a class weapon")
					for it: ItemInstance in items:
						ok(it.rarity >= (BH.Rarity.MASTER if boss else BH.Rarity.ELITE), "every piece meets quality floor")
						ok(ItemGenerator.class_fit(it.base, cls) or (it.base.category == &"accessory" and it.base.class_hint == &""), "%s fits %s" % [it.base.id, cls])
				e.free()
		p.free()
	Loot.rng.state = saved_rng
	# There are no low-level ranger sets: a guaranteed roll must not fall back to a mage set.
	eq(ItemGenerator.random_special(rng(4), 1, true, &"ranger", 1.0), null, "no eligible special means no incompatible fallback")
	done()

func test_map_owner_stays_with_existing_explorer() -> void:
	var members := {1: {"map": "sanctuary"}, 20: {"map": "westreach"}, 30: {"map": "westreach"}}
	eq(Net.choose_world_owner(members, "westreach", 30), 30, "existing owner keeps its world")
	members[1].map = "westreach"
	eq(Net.choose_world_owner(members, "westreach", 30), 30, "leader arriving does not reset an ally's monsters")
	members.erase(30)
	eq(Net.choose_world_owner(members, "westreach", 30), 1, "remaining member takes over")
	eq(Net.choose_world_owner(members, "ruined_forest", 0), 0, "empty maps have no owner")
	ok(Net.may_travel(), "party travel never requires leader permission")
	eq(Net.portal_error(1), "Join a party first.", "offline portals are refused")
	done()
