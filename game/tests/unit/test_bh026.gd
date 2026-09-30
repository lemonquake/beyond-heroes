extends TestCase
## bh-026: the Ember Dragon set (DataSpecialWeapons) — Aljay's last Legendary set from the sculpts in
## models/special_weapons/: three Legendary story pieces, knights only, fitted models and icons, and the "alj" code's
## Unbound copies (no level or attributes, wearable from Class E, four sockets).

const IDS := [&"ember_dragonslayer", &"aegis_of_fragnir", &"ember_dragonhide"]

func _knight(tier := 1) -> HeroData:
	var h := Game.new_hero(&"knight", "Ember")
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	h.guild = &"swordfin"
	h.set_tier(tier)
	return h

func _alj(h: HeroData) -> Array:
	Cheats.apply("alj", h)
	return h.inventory.cells.filter(func(c): return c != null and IDS.has(c.base.id))

# ---- The pieces ---------------------------------------------------------------------------------------------------

func test_three_legendary_story_pieces() -> void:
	eq(DataSpecialWeapons.ids(), IDS, "sword, shield, cuirass")
	var cats := {&"ember_dragonslayer": &"weapon", &"aegis_of_fragnir": &"shield", &"ember_dragonhide": &"armor"}
	for id in IDS:
		var b := DB.item_base(id)
		ok(b != null, "%s is an item base" % id)
		if b == null:
			continue
		eq(b.category, cats[id], "%s category" % id)
		eq(b.fixed_rarity, BH.Rarity.LEGENDARY, "%s is Legendary" % id)
		eq(b.set_id, DataSpecialWeapons.SET_ID, "%s belongs to the Ember Dragon set" % id)
		ok(b.story and b.drop_weight == 0, "%s is a story piece" % id)
		eq(b.wearers, [&"knight", &"swordsman", &"warden"], "%s: knights only" % id)
		ok(b.lore != "" and b.unique_name != "", "%s has a name and lore" % id)
		var it := DB.make_item(id, BH.Rarity.COMMON, 30, 1)
		eq(it.rarity, BH.Rarity.LEGENDARY, "%s is made Legendary" % id)
	var sw := DB.item_base(&"ember_dragonslayer")
	eq(sw.weapon_type, &"sword", "the Dragonslayer is a sword")
	eq(sw.element, Elements.FIRE, "with a fire edge")
	ok(DB.item_base(&"aegis_of_fragnir").block_chance > 0.0, "the Aegis blocks")
	ok(DB.item_base(&"ember_dragonhide").defense > DB.item_base(&"boss_dragonforge_armor").defense, "the Dragonhide outguards a boss cuirass")
	done()

func test_models_and_icons() -> void:
	for id in IDS:
		var b := DB.item_base(id)
		eq(b.model_path(), "res://assets/items/%s.glb" % id, "%s has its own model" % id)
		ok(ResourceLoader.exists(b.icon_path()) and b.icon_path().contains("items3d"), "%s has its 3D icon" % id)
		var n := ItemModels.instance(b)
		var bb := ItemModels.bounds(n)
		ok(bb.size.length() > 0.3, "%s model has size (%s)" % [id, bb.size])
		n.free()
	# the sculpted sword and shield keep their painted colours: vertex colour as albedo (BH_Baked)
	for id in [&"ember_dragonslayer", &"aegis_of_fragnir"]:
		var n := ItemModels.instance(DB.item_base(id))
		var mis := n.find_children("*", "MeshInstance3D", true, false)
		ok(not mis.is_empty(), "%s has a mesh" % id)
		for mi: MeshInstance3D in mis:
			var arrays := mi.mesh.surface_get_arrays(0)
			ok(arrays[Mesh.ARRAY_COLOR] != null and (arrays[Mesh.ARRAY_COLOR] as PackedColorArray).size() > 0, "%s carries its colours" % id)
			var mat := mi.get_surface_override_material(0) as StandardMaterial3D
			ok(mat != null and mat.vertex_color_use_as_albedo, "%s draws them" % id)
		n.free()
	# hand-socket conventions: the sword's grip at the origin (blade up +Y), the shield's handle behind its face
	var sword := ItemModels.bounds(ItemModels.instance(DB.item_base(&"ember_dragonslayer")))
	ok(sword.position.y < -0.05 and sword.end.y > 0.8, "the sword is held at its grip, blade up (%s)" % sword)
	var shield := ItemModels.bounds(ItemModels.instance(DB.item_base(&"aegis_of_fragnir")))
	ok(shield.end.z > 0.05 and shield.position.z > -0.08, "the shield's face is in front of the hand (%s)" % shield)
	near(shield.size.y, 0.84, 0.02, "the shield is 0.84 m tall")
	done()

func test_worn_cuirass_fits_the_hero() -> void:
	ok(HeroWear.has_model("ember_dragonhide"), "the fitted cuirass exists")
	var h := _knight()
	h.equipment.slots[&"armor"] = DB.make_item(&"ember_dragonhide", BH.Rarity.LEGENDARY, 30, 1)
	var plan := HeroWear.plan(h.equipment)
	ok(plan.pieces.any(func(p): return p.id == "ember_dragonhide"), "the hero wears it")
	var v := CharacterVisual.new()
	host.add_child(v)
	v.setup(HeroLook.MODEL, 1.0, Color(0.7, 0.2, 0.2), &"knight")
	var parts := HeroWear.build({"id": "ember_dragonhide", "side": "", "skip": []}, v.skeleton)
	ok(not parts.is_empty(), "built on the hero's skeleton")
	var tris := 0
	for mi: MeshInstance3D in parts:
		ok(mi.skin != null, "skinned to the bones")
		for s in mi.mesh.get_surface_count():
			tris += (mi.mesh.surface_get_arrays(s)[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
		ok(mi.mesh.get_blend_shape_count() >= 4, "follows the body sliders")
		mi.free()
	ok(tris > 3000 and tris <= 7200, "within the armour budget (%d triangles)" % tris)
	v.free()
	done()

func test_tempo_wears_the_cuirass() -> void:
	var cls := DB.class_def(&"knight")
	var v := CharacterVisual.new()
	host.add_child(v)
	v.setup(cls.model_path, 1.0, cls.tint, &"knight")
	var eqp := Equipment.new()
	eqp.slots[&"armor"] = DB.make_item(&"ember_dragonhide", BH.Rarity.LEGENDARY, 30, 1)
	v.dress_equipment(eqp)
	ok(v._set_nodes.any(func(n): return String(n.name) == "Set_special_armor"), "a knight-type body wears it on its chest")
	eqp.slots[&"armor"] = null
	v.dress_equipment(eqp)
	eq(v._set_nodes.size(), 0, "and takes it off")
	v.free()
	done()

# ---- Knights only ---------------------------------------------------------------------------------------------------

func test_only_knights_wear_it() -> void:
	for cls_id in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := Game.new_hero(cls_id, "Tryer")
		h.equipment.tier_rank = DataGuilds.MAX_RANK
		var attrs := {&"str": 999, &"dex": 999, &"int": 999, &"agi": 999, &"vit": 999}
		for id in IDS:
			var it := DB.make_item(id, BH.Rarity.LEGENDARY, 30, 1)
			var err := h.equipment.check(it, h.equipment.auto_slot(it), 60, attrs)
			if cls_id == &"knight":
				eq(err, "", "a Knight wears %s" % id)
			else:
				ok(err.contains("Knights"), "a %s cannot wear %s (%s)" % [cls_id, id, err])
	# Tempos: the knight-type Swordsman and Warden, not the others
	var hero := _knight(8)
	hero.progress.add_xp(XpCurve.total_xp_for_level(60))
	for tc in DataTempos.CLASSES:
		var t := TempoData.new()
		t.class_id = tc
		var it := DB.make_item(&"ember_dragonhide", BH.Rarity.LEGENDARY, 30, 1)
		it.unbound = true
		var err := TempoRules.equip_error(hero, t, it, &"armor")
		if tc in [&"swordsman", &"warden"]:
			eq(err, "", "a %s Tempo wears it" % tc)
		else:
			ok(err.contains("Knights"), "a %s Tempo cannot (%s)" % [tc, err])
	done()

func test_never_generated() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 26
	var seen := false
	for i in 3000:
		var b := ItemGenerator.random_special(rng, 60, i % 2 == 0, &"knight", 1.0)
		if b != null and DataSpecialWeapons.is_special(b):
			seen = true
	ok(not seen, "no loot roll makes an Ember Dragon piece")
	done()

# ---- "alj" ----------------------------------------------------------------------------------------------------------

func test_alj_gives_the_set() -> void:
	var h := _knight(1)
	var got := _alj(h)
	eq(got.size(), 3, "all three pieces")
	for it: ItemInstance in got:
		ok(it.unbound and it.rarity == BH.Rarity.LEGENDARY, "%s: a Legendary Unbound copy" % it.base.id)
		eq(it.sockets, 4, "%s: four sockets open" % it.base.id)
		eq(it.gems, ["", "", "", ""], "%s: empty" % it.base.id)
		var back := ItemInstance.from_dict(JSON.parse_string(JSON.stringify(it.to_dict())))
		ok(back.unbound and back.sockets == 4 and back.gems.size() == 4, "%s keeps both through a save" % it.base.id)
	done()

func test_alj_set_worn_at_class_e() -> void:
	var h := _knight(1)
	eq(h.progress.level, 1, "a level-1 hero")
	eq(DataGuilds.letter(h.tier), "E", "of Class E")
	for it: ItemInstance in _alj(h):
		eq(h.equip_from_inventory(it), "", "wears %s (no level, attribute or Legendary rank gate)" % it.base.id)
	eq(h.equipment.get_item(&"main_weapon").base.id, &"ember_dragonslayer", "sword in hand")
	eq(h.equipment.get_item(&"sub_weapon").base.id, &"aegis_of_fragnir", "shield on the arm")
	eq(h.equipment.get_item(&"armor").base.id, &"ember_dragonhide", "cuirass on")
	eq(int(h.equipment.set_counts().get(DataSpecialWeapons.SET_ID, 0)), 3, "the whole set")
	var st := h.compute_stats()
	near(st.flag(&"hit_ignite"), 0.15, 0.0001, "the full set ignites")
	# an ordinary Legendary copy still asks for Class B, level 30 and 40 Strength
	var plain := DB.make_item(&"ember_dragonhide", BH.Rarity.LEGENDARY, 30, 1)
	ok(h.equipment.check(plain, &"armor", 1, h.progress.base_attributes()) != "", "a plain copy is out of reach")
	done()

func test_alj_needs_class_e() -> void:
	var h := Game.new_hero(&"knight", "Unranked")
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	eq(h.tier, 0, "Unranked")
	for it: ItemInstance in _alj(h):
		ok(h.equip_from_inventory(it).contains("Class E"), "an Unranked hero needs Class E for %s" % it.base.id)
	done()

func test_alj_for_a_mage() -> void:
	var h := Game.new_hero(&"mage", "NotAKnight")
	h.guild = &"lantern"
	h.set_tier(3)
	var line := Cheats.apply("alj", h)
	ok(line.contains("Knights only"), "the code says who can wear them (%s)" % line)
	for c in h.inventory.cells:
		if c != null and IDS.has(c.base.id):
			ok(h.equip_from_inventory(c) != "", "a mage cannot wear %s" % c.base.id)
	done()
