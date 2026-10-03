extends TestCase
## bh-024: the Leggings slot — its catalogue (class leggings, set and depth pieces, uniques, the fifteen boss Legguards),
## loot, merchants, the paper dolls, saves, and how leggings are worn on the hero body (HeroWear) and on the regalia.

func _init() -> void:
	strict = true

func _leggings(boss := false) -> Array:
	var out := []
	for b: ItemBaseDef in DB.item_bases.values():
		# bh-034: the Ascendant legguards are regalia with their own suite (test_bh034)
		if b.category == &"leggings" and b.boss_exclusive == boss and not DataAscendant.is_ascendant(b):
			out.append(b)
	return out

func _visual() -> CharacterVisual:
	var v := CharacterVisual.new()
	host.add_child(v)
	v.setup(HeroLook.MODEL, 1.0, Color(0.7, 0.2, 0.2), &"knight")
	return v

func _equip(e: Equipment, ids: Array) -> void:
	for id in ids:
		var it := DB.make_item(StringName(id), BH.Rarity.COMMON, 1, 3)
		e.slots[e.auto_slot(it)] = it

# ---- The slot ----------------------------------------------------------------------------------------------------

func test_the_slot() -> void:
	ok(BH.SLOTS.has(&"leggings"), "Leggings is an equipment slot")
	eq(BH.SLOTS.size(), 14, "fourteen slots")
	eq(BH.SLOT_NAMES.get(&"leggings"), "Leggings", "its name")
	eq(BH.CATEGORY_SLOTS.get(&"leggings"), [&"leggings"], "leggings go in the Leggings slot only")
	var e := Equipment.new()
	ok(e.slots.has(&"leggings"), "equipment has the slot")
	var it := DB.make_item(&"iron_cuisses", BH.Rarity.COMMON, 1, 1)
	eq(e.auto_slot(it), &"leggings", "auto slot")
	eq(e.check(it, &"leggings", 1, {&"str": 10}), "", "fits")
	ok(e.check(it, &"armor", 1, {&"str": 10}) != "", "not in the armour slot")
	ok(e.check(DB.make_item(&"iron_hauberk", BH.Rarity.COMMON, 1, 1), &"leggings", 1, {&"str": 20}) != "", "armour is not leggings")
	var r := e.equip(it, &"leggings", 1, {&"str": 10})
	ok(r.ok, "equips")
	ok(e.modifiers().any(func(m): return m.stat == &"max_hp"), "its implicit counts")
	eq(e.slot_of(it), &"leggings", "slot_of")
	done()

func test_saves_old_and_new() -> void:
	var e := Equipment.new()
	_equip(e, [&"magister_silks", &"magister_robe"])
	var back := Equipment.new()
	back.from_dict(e.to_dict())
	ok(back.get_item(&"leggings") != null and back.get_item(&"leggings").base.id == &"magister_silks", "leggings survive a save")
	var old := e.to_dict()
	old.erase("leggings")                         # a save from before bh-024
	var legacy := Equipment.new()
	legacy.from_dict(old)
	eq(legacy.get_item(&"leggings"), null, "an old save loads with the slot empty")
	ok(legacy.get_item(&"armor") != null, "and everything else in place")
	done()

func test_every_class_starts_in_leggings() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := Game.new_hero(cls, "Legs")
		var it := h.equipment.get_item(&"leggings")
		ok(it != null, "%s starts in leggings" % cls)
		if it:
			eq(it.base.class_hint, cls, "%s leggings suit the class" % cls)
	done()

# ---- The catalogue ------------------------------------------------------------------------------------------------

func test_catalogue() -> void:
	var plain := _leggings(false)
	ok(plain.size() >= 30, "at least thirty unique leggings (%d)" % plain.size())
	var names := {}
	var per_class := {}
	for b: ItemBaseDef in plain:
		var nm: String = b.unique_name if b.unique_name != "" else b.display_name
		ok(not names.has(nm), "%s is unique" % nm)
		names[nm] = true
		per_class[b.class_hint] = int(per_class.get(b.class_hint, 0)) + 1
		ok(b.defense > 0.0, "%s protects" % b.id)
		ok(b.class_hint in [&"knight", &"mage", &"ranger", &"shadowblade"], "%s belongs to a class" % b.id)
		ok(ResourceLoader.exists(b.icon), "%s has its own icon" % b.id)
		ok(b.model_path() == ItemBaseDef.ITEM_MODEL % b.id, "%s has its own item model" % b.id)
		ok(HeroWear.has_model(String(b.id)), "%s has its own worn model" % b.id)
		ok(b.weight > 0.0 and b.weight <= 9.0, "%s weighs something sensible (%.2f)" % [b.id, b.weight])
		eq(b.weight_class == &"heavy", b.class_hint == &"knight", "%s: only knights wear plate legs" % b.id)
	for cls in per_class:
		ok(int(per_class[cls]) >= 7, "%s has a range of leggings (%d)" % [cls, per_class[cls]])
	var uniques := plain.filter(func(b): return b.unique_name != "" and not String(b.id).begins_with("depth_"))
	ok(uniques.size() >= 8, "named unique leggings (%d)" % uniques.size())
	for b: ItemBaseDef in uniques:
		var it := DB.make_item(b.id, BH.Rarity.COMMON, b.level_req, 5)
		eq(it.rarity, b.fixed_rarity, "%s keeps its rarity" % b.unique_name)
		for p in b.fixed_powers:
			ok(it.powers.has(String(p)), "%s has its power %s" % [b.unique_name, p])
			ok(DB.power(p) != null, "power %s exists" % p)
	for fb in ["leggings_plate", "leggings_cloth", "leggings_leather"]:
		ok(ResourceLoader.exists("res://assets/ui/icons/items/%s.svg" % fb), "fallback icon %s" % fb)
	done()

func test_set_pieces() -> void:
	for pair in [[&"aether_guardian", &"guardian_cuisses"], [&"starbound_sage", &"sage_leggings"]]:
		var s := DB.item_set(pair[0])
		ok(s.pieces.has(pair[1]), "%s includes %s" % pair)
		eq(DB.item_base(pair[1]).set_id, pair[0], "%s knows its set" % pair[1])
		ok(s.bonuses.has(6), "%s rewards all six pieces" % pair[0])
	var depth := 0
	for b: ItemBaseDef in _leggings(false):
		if String(b.id).begins_with("depth_"):
			depth += 1
			eq(b.level_req, 44, "%s sits between the crown and the grips" % b.id)
	eq(depth, 4, "each depth group has its leg piece")
	done()

func test_boss_legguards() -> void:
	var boss := _leggings(true)
	eq(boss.size(), DataBossSets.ROWS.size(), "one Legguards piece for each boss collection")
	for row in DataBossSets.ROWS:
		var sid := StringName(row[0])
		var id := DataBossSets.piece_id(sid, &"leggings")
		var b := DB.item_base(id)
		ok(b != null, "%s has Legguards" % sid)
		if b == null:
			continue
		ok(DB.item_set(sid).pieces.has(id), "%s counts toward the set" % id)
		ok(b.display_name.ends_with("Legguards"), "named %s" % b.display_name)
		eq(b.equip_slots, [&"leggings"], "worn in the Leggings slot")
		ok(ResourceLoader.exists(b.model_path()), "%s has its regalia model" % id)
		ok(ResourceLoader.exists(b.icon), "%s has its icon" % id)
		var scene: Node = (load(b.model_path()) as PackedScene).instantiate()
		ok(scene.find_child("AT_thigh_L", true, false) != null and scene.find_child("AT_thigh_R", true, false) != null,
			"%s follows both thighs" % id)
		scene.free()
	done()

# ---- Loot and merchants ---------------------------------------------------------------------------------------------

func test_loot_and_affixes() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var seen := 0
		for i in 40:
			var b := ItemGenerator.random_base(rng(i + 7), 30, [&"leggings"], cls, 1.0)
			if b != null:
				eq(b.category, &"leggings", "leggings drop as leggings")
				ok(ItemGenerator.class_fit(b, cls), "%s gets its own leggings (%s)" % [cls, b.id])
				seen += 1
		ok(seen == 40, "%s always finds leggings to drop" % cls)
	ok(DB.affixes_for(&"leggings").size() >= 20, "leggings roll armour enchantments (%d)" % DB.affixes_for(&"leggings").size())
	for tier in [&"mythical", &"legendary", &"aether", &"relic"]:
		ok(DB.powers_for(&"leggings").any(func(p): return p.tier == tier), "leggings can carry a %s power" % tier)
	var it := DB.make_item(&"warden_cuisses", BH.Rarity.LEGENDARY, 30, 11)
	ok(it.powers.size() >= 1, "a Legendary pair rolls its power")
	eq(DataCrystals.group_for(&"leggings"), DataCrystals.group_for(&"armor"), "crystals set in leggings act as in armour")
	done()

func test_merchants_sell_leggings() -> void:
	var sellers := 0
	for def: ShopDef in DB.shops.values():
		if def.specialties.has(&"armor"):
			ok(def.specialties.has(&"leggings"), "%s deals in leggings too" % def.id)
			var pools: Array = def.pools
			ok(pools.any(func(p): return (p.get("categories", []) as Array).has(&"leggings")), "%s stocks leggings" % def.id)
			sellers += 1
	ok(sellers >= 3, "every armour merchant (%d)" % sellers)
	var h := Game.new_hero(&"ranger", "Shopper")
	var s := Shop.open(DB.shop(&"brannoc_forge"), h)
	ok(s.stock.any(func(e): return e.item.base.category == &"leggings"), "the smith's rack has leggings")
	done()

# ---- The paper dolls ------------------------------------------------------------------------------------------------

func test_paper_dolls() -> void:
	for layout in [InventoryWindow.SLOT_LAYOUT, TempoWindow.SLOT_LAYOUT]:
		var taken := {}
		for slot in BH.SLOTS:
			if slot in [&"main_weapon", &"sub_weapon"]:
				continue
			ok(layout.has(slot), "%s has a place on the doll" % slot)
			var key := str(layout.get(slot))
			ok(not taken.has(key), "%s has a place of its own" % slot)
			taken[key] = true
	eq(InventoryWindow.GLYPH.get(&"leggings"), "leggings", "its empty-slot glyph")
	ok(ResourceLoader.exists("res://assets/ui/slots/glyph_leggings.png"), "the glyph exists")
	var t := Tips.text("x", "y")
	ok(t != null, "tooltips build")
	t.free()
	ok(DataCrafting.ARMOR_VARIANTS.any(func(v): return (v[1] as Array).has(&"leggings")), "crafters can make leggings")
	done()

# ---- Worn on the hero ---------------------------------------------------------------------------------------------

func test_worn_leggings_and_what_covers_them() -> void:
	# bare legs with leggings alone: all of it shows
	var e := Equipment.new()
	_equip(e, [&"commander_cuisses"])
	var plan := HeroWear.plan(e)
	var legs: Dictionary = plan.pieces.filter(func(p): return p.id == "commander_cuisses")[0]
	eq(legs.get("skip", []), [], "nothing over them: belt, tassets, plates, knees, cuffs all show")
	ok(plan.pieces.any(func(p): return p.id == HeroWear.SHOES), "shoes with leggings and no boots")
	ok(not plan.pieces.any(func(p): return p.id == HeroWear.BREECHES), "leggings replace the plain breeches")
	var z: Vector2 = plan.hide.get("z1", HeroWear.FAR)
	ok(z.x < 0.2 and z.y > 1.0, "the legs are cut from the skin (%s)" % z)
	# a shirt: the belt goes under it
	_equip(e, [&"padded_gambeson"])
	legs = HeroWear.plan(e).pieces.filter(func(p): return p.id == "commander_cuisses")[0]
	eq(legs.skip, ["waist"], "a shirt closes over the belt")
	# a hauberk's skirt: the thigh plates go too
	_equip(e, [&"iron_hauberk"])
	legs = HeroWear.plan(e).pieces.filter(func(p): return p.id == "commander_cuisses")[0]
	eq(legs.skip, ["waist", "hip"], "a skirt to the knee hides the thigh plates")
	# a robe to the shins: the knee cops too; and boots swallow the cuffs
	var m := Equipment.new()
	_equip(m, [&"magister_robe", &"arcanist_legwraps", &"sage_boots"])
	m.slots[&"boots_2"] = DB.make_item(&"sage_boots", BH.Rarity.COMMON, 1, 4)
	legs = HeroWear.plan(m).pieces.filter(func(p): return p.id == "arcanist_legwraps")[0]
	eq(legs.skip, ["waist", "hip", "knee", "ankle_L", "ankle_R"], "a robe and boots over wrapped legs")
	# a coat without leggings: plain breeches
	var c := Equipment.new()
	_equip(c, [&"traveler_coat"])
	ok(HeroWear.plan(c).pieces.any(func(p): return p.id == HeroWear.BREECHES), "nobody goes bare-legged in a coat")
	done()

func test_worn_leggings_on_the_body() -> void:
	var v := _visual()
	var h := Game.new_hero(&"knight", "Legs")
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	_equip(h.equipment, [&"warden_cuisses"])
	v.dress_equipment(h.equipment)
	var names: Array = v.hero._wear.map(func(m): return String(m.name))
	ok(names.has("Wear_warden_cuisses"), "the leggings are worn (%s)" % [names])
	for m: MeshInstance3D in v.hero._wear:
		eq(m.get_parent(), v.skeleton, "on the skeleton")
		ok(m.skin != null, "skinned")
	var tris := 0
	for b: ItemBaseDef in _leggings(false):
		var meshes := HeroWear.build({"id": String(b.id), "side": ""}, v.skeleton)
		ok(not meshes.is_empty(), "%s builds" % b.id)
		tris = 0
		for mi in meshes:
			for s in mi.mesh.get_surface_count():
				tris += mi.mesh.surface_get_array_index_len(s) / 3
			ok(mi.mesh.get_surface_count() <= 6, "%s uses few materials (%d)" % [b.id, mi.mesh.get_surface_count()])
			for k in HeroLook.BODY_KEYS:
				if String(mi.name) == "Wear_" + String(b.id):
					ok(mi.find_blend_shape_by_name(StringName(k)) >= 0, "%s follows the %s slider" % [b.id, k])
			mi.free()
		ok(tris <= 6500, "%s within its triangle budget (%d)" % [b.id, tris])
	# the groups the game leaves off are separate meshes
	var parts := HeroWear.build({"id": "commander_cuisses", "side": "", "skip": ["waist", "hip"]}, v.skeleton)
	var got: Array = parts.map(func(mi): return String(mi.name))
	eq(got.size(), 2, "cloth and knees stay when the belt and the plates are skipped (%s)" % [got])
	for mi in parts:
		mi.free()
	for id in [HeroWear.BREECHES, HeroWear.UNDER_LEGS]:
		ok(HeroWear.has_model(id), "shared piece %s" % id)
	v.free()
	done()

func test_boss_legguards_on_the_hero() -> void:
	var h := Game.new_hero(&"knight", "Regal")
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	h.equipment.slots[&"leggings"] = DB.make_item(&"boss_crimson_glory_leggings", BH.Rarity.MASTER, 30, 5)
	var plan := HeroWear.plan(h.equipment)
	ok(plan.pieces.any(func(p): return p.id == HeroWear.UNDER_LEGS), "a plain under-layer beneath the Legguards")
	ok(not plan.pieces.any(func(p): return p.id == HeroWear.BREECHES), "no breeches under Legguards")
	var v := _visual()
	v.dress_equipment(h.equipment)
	var thighs := v._set_nodes.filter(func(n): return String(n.name).begins_with("SetPart_leggings_thigh"))
	eq(thighs.size(), 2, "the thigh plates ride both thighs")
	v.free()
	done()

# ---- Unbound items and "alj" --------------------------------------------------------------------------------------

func test_unbound_items_have_no_requirements() -> void:
	var h := Game.new_hero(&"mage", "Unbound")
	h.equipment.tier_rank = 0
	var it := DB.make_item(&"u_oathbound_cuisses", BH.Rarity.LEGENDARY, 40, 9)
	var attrs := h.progress.base_attributes()
	ok(h.equipment.check(it, &"leggings", 1, attrs) != "", "a level-40 Legendary is out of a new mage's reach")
	it.unbound = true
	ok(h.equipment.check(it, &"leggings", 1, attrs).contains("Class E"), "bh-026: Unbound gear asks for Class E")
	h.equipment.tier_rank = 1
	eq(h.equipment.check(it, &"leggings", 1, attrs), "", "Unbound: no level or attribute requirement, Class E is enough")
	ok(h.equipment.check(it, &"armor", 1, attrs) != "", "but it still only fits its own slot")
	var back := ItemInstance.from_dict(JSON.parse_string(JSON.stringify(it.to_dict())))
	ok(back.unbound, "Unbound survives a save")
	ok(not ItemInstance.from_dict(DB.make_item(&"iron_cuisses", BH.Rarity.COMMON, 1, 1).to_dict()).unbound, "ordinary items are not")
	h.inventory.add(it)
	eq(h.equip_from_inventory(it), "", "a level-1 mage wears it")
	eq(h.equipment.get_item(&"leggings"), it, "in the Leggings slot")
	var sw := DataSpecialWeapons.unbound(&"u_riftblade", 1)
	ok(sw != null and sw.unbound and sw.base.is_weapon(), "any base can be made Unbound")
	done()

func test_alj() -> void:
	ok(Cheats.is_code("alj") and Cheats.is_code("  ALJ "), "alj is a code")
	var h := Game.new_hero(&"knight", "Alj")
	var before := h.inventory.cells.filter(func(c): return c != null).size()
	var line := Cheats.apply("alj", h)
	ok(line.begins_with("Cheat:"), "alj answers (%s)" % line)
	var after := h.inventory.cells.filter(func(c): return c != null).size()
	eq(after - before, DataSpecialWeapons.ids().size(), "one Unbound piece for each special weapon")
	for c in h.inventory.cells:
		if c != null and DataSpecialWeapons.ids().has(c.base.id):
			ok(c.unbound and c.rarity == BH.Rarity.LEGENDARY, "%s is a Legendary Unbound variant" % c.base.id)
	done()
