extends TestCase
## bh-017: class-biased equipment drops, five new buffs and debuffs (with healing reduction), weapon Enchantment and
## Fore-Tech, the hero's own guild name and banner, town shop districts, and the Quake Team allies.

func _init() -> void:
	strict = true

func _hero(cls := &"knight", level := 1) -> HeroData:
	var h := Game.new_hero(cls, "Tester")
	h.progress.level = level
	return h

# ---- class-biased drops -------------------------------------------------------------------------------------------

func test_drops_favour_the_heros_class() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		for ilvl in [6, 14, 26]:
			var r := rng(ilvl * 31 + 7)
			var fit := 0
			var n := 1500
			for i in n:
				var b := ItemGenerator.random_base(r, ilvl, [], cls)
				if b != null and ItemGenerator.class_fit(b, cls):
					fit += 1
			var share := float(fit) / float(n)
			ok(share >= 0.65, "%s at item level %d: %.0f%% of gear drops are class gear (need 65%%)" % [cls, ilvl, share * 100.0])
	done()

func test_class_fit_rules() -> void:
	var sword := DB.item_base(&"iron_longsword")
	var staff := DB.item_base(&"ashwood_staff")
	var plate := DB.item_base(&"iron_hauberk")
	var robe := DB.item_base(&"apprentice_robe")
	ok(ItemGenerator.class_fit(sword, &"knight"), "a sword is knight gear")
	ok(not ItemGenerator.class_fit(sword, &"mage"), "a sword is not mage gear")
	ok(ItemGenerator.class_fit(staff, &"mage"), "a staff is mage gear")
	ok(ItemGenerator.class_fit(plate, &"knight") and not ItemGenerator.class_fit(plate, &"mage"), "plate is for knights")
	ok(ItemGenerator.class_fit(robe, &"mage") and not ItemGenerator.class_fit(robe, &"knight"), "a robe is for mages")
	ok(ItemGenerator.class_fit(DB.item_base(&"warden_kite_shield"), &"knight"), "shields are knight gear")
	ok(not ItemGenerator.class_fit(DB.item_base(&"copper_ring"), &"knight"), "rings are nobody's class gear")
	ok(not ItemGenerator.class_fit(sword, &""), "no class, no fit")
	done()

func test_no_class_keeps_the_old_pool() -> void:
	var r := rng(5)
	var seen := {}
	for i in 600:
		var b := ItemGenerator.random_base(r, 20)
		if b:
			seen[b.category] = true
	ok(seen.size() >= 6, "without a class hint every category still drops (%d)" % seen.size())
	done()

# ---- world scaffolding ----------------------------------------------------------------------------------------------

var _holder: Node3D
var _saved := {}
var _player: Player

func _begin(map_id: StringName, spawn: StringName = &"start") -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "Bh017World"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Tester17")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, spawn)
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	for t in TempoParty.actors(host.get_tree()):
		t.free()
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

# ---- new buffs and debuffs ------------------------------------------------------------------------------------------

const NEW_DEBUFFS := [&"grievous", &"enfeebled", &"dazzled", &"sundered", &"demoralized"]
const NEW_BUFFS := [&"vigor", &"keen", &"windstep", &"titan", &"spirit_ward"]

func test_five_new_buffs_and_debuffs_exist() -> void:
	for id in NEW_DEBUFFS:
		ok(StatusRules.DEFS.has(id) and StatusRules.is_debuff(id), "%s is a debuff" % id)
		ok(ResourceLoader.exists(StatusRules.icon_of(id)), "%s has an icon" % id)
		ok(StatusRules.desc_of(id) != "", "%s explains itself" % id)
	for id in NEW_BUFFS:
		ok(StatusRules.DEFS.has(id) and not StatusRules.is_debuff(id), "%s is a buff" % id)
		ok(ResourceLoader.exists(StatusRules.icon_of(id)), "%s has an icon" % id)
	done()

func test_grievous_wound_lowers_healing_and_regen() -> void:
	eq(StatusRules.heal_taken(&"grievous"), -0.25, "a Grievous Wound starts at 25% less healing")
	var st := StatusController.new()
	near(st.heal_taken_mult(), 1.0, 0.0001, "no wound, full healing")
	st.apply(&"grievous")
	near(st.heal_taken_mult(), 0.75, 0.0001, "one wound: 25% reduction")
	st.apply(&"grievous")
	near(st.heal_taken_mult(), 0.5, 0.0001, "two wounds: 50%")
	st.apply(&"grievous")
	st.apply(&"grievous")
	near(st.heal_taken_mult(), 0.25, 0.0001, "three wounds is the most (75%)")
	eq(st.stacks(&"grievous"), 3, "the wound stops deepening at 3")
	var vig := StatusController.new()
	vig.apply(&"vigor")
	near(vig.heal_taken_mult(), 1.25, 0.0001, "Vigor raises healing received")
	var both := StatusController.new()
	both.apply(&"grievous")
	both.apply(&"purged")
	near(both.heal_taken_mult(), 0.375, 0.0001, "Purged still halves it")
	# through a real actor: Actor.heal
	var a := Actor.new()
	a.stats = TestCase.blank_stats()
	a.hp = 100.0
	a.heal(200.0, false)
	near(a.hp, 300.0, 0.001, "an unwounded actor heals fully")
	a.hp = 100.0
	a.status.apply(&"grievous")
	a.heal(200.0, false)
	near(a.hp, 250.0, 0.001, "a wounded actor heals 25% less")
	a.free()
	done()

func test_stat_debuffs_and_buffs_change_the_right_stats() -> void:
	var h := _hero(&"knight", 10)
	var base := h.compute_stats()
	var cases := {
		&"enfeebled": [&"str", -1.0], &"dazzled": [&"evasion", -1.0], &"sundered": [&"defense", -1.0], &"demoralized": [&"outgoing_damage", -1.0],
		&"titan": [&"str", 1.0], &"keen": [&"crit_chance", 1.0], &"windstep": [&"evasion", 1.0], &"vigor": [&"max_hp", 1.0],
		&"spirit_ward": [&"res_fire", 1.0],
	}
	for id in cases:
		var st := StatusController.new()
		st.apply(id)
		var s := h.compute_stats(st.stat_modifiers())
		var stat: StringName = cases[id][0]
		var dir: float = cases[id][1]
		var d := s.get_stat(stat, 1.0) - base.get_stat(stat, 1.0)
		ok(d * dir > 0.0, "%s moves %s the right way (%.3f -> %.3f)" % [id, stat, base.get_stat(stat, 1.0), s.get_stat(stat, 1.0)])
	done()

func test_every_enemy_and_skill_status_is_defined() -> void:
	var n := 0
	var used := {}
	for e: EnemyDef in DB.enemies.values():
		for a in e.attacks:
			for k in (a as Dictionary).get("status", {}):
				n += 1
				used[k] = true
				ok(StatusRules.DEFS.has(StringName(k)), "%s.%s inflicts a defined status (%s)" % [e.id, a.get("id", "?"), k])
			for k in (a as Dictionary).get("on_hit_status", {}):
				ok(StatusRules.DEFS.has(StringName(k)), "%s.%s on-hit status %s is defined" % [e.id, a.get("id", "?"), k])
	ok(n > 30, "%d enemy statuses checked" % n)
	for id in [&"grievous", &"sundered", &"demoralized", &"enfeebled", &"dazzled"]:
		ok(used.has(id) or used.has(String(id)), "some monster inflicts %s" % id)
	for sid in [&"shield_bash", &"judgment", &"eviscerate", &"crippling_star"]:
		var sk := DB.skill(sid)
		ok(sk != null and not sk.on_hit_status.is_empty(), "%s inflicts a status" % sid)
		if sk:
			for k in sk.on_hit_status:
				ok(StatusRules.DEFS.has(StringName(k)), "%s status %s is defined" % [sid, k])
	done()

func test_new_consumables_work_and_can_be_had() -> void:
	var elixirs := {&"vigor_draught": &"vigor", &"keen_tonic": &"keen", &"windstep_tonic": &"windstep", &"titan_brew": &"titan", &"spirit_ward_draught": &"spirit_ward"}
	for id in elixirs:
		var b := DB.item_base(id)
		ok(b != null and b.is_consumable(), "%s is a consumable" % id)
		if b:
			eq(StringName(b.consumable_effect.get("buff", "")), elixirs[id], "%s grants %s" % [id, elixirs[id]])
		ok(not DataCrafting.recipe(id).is_empty(), "%s can be brewed" % id)
	for id in [&"blinding_flask", &"festering_bomb"]:
		var b2 := DB.item_base(id)
		ok(b2 != null and b2.consumable_effect.has("throw"), "%s is thrown" % id)
		if b2:
			ok(StatusRules.DEFS.has(StringName(b2.consumable_effect.throw.status)), "%s inflicts a defined status" % id)
		ok(not DataCrafting.recipe(id).is_empty(), "%s can be made" % id)
	var sold := 0
	for sd in DataShops.build():
		for f in sd.fixed:
			if elixirs.has(StringName(f.base)) or f.base in [&"blinding_flask", &"festering_bomb"]:
				sold += 1
	ok(sold >= 9, "the merchants stock them (%d listings)" % sold)
	done()

# ---- weapon Enchantment and Fore-Tech -------------------------------------------------------------------------------

func _stock(h: HeroData, ids: Dictionary) -> void:
	for id in ids:
		var it := DB.make_item(id, BH.Rarity.COMMON, 1, 5)
		it.count = int(ids[id])
		h.inventory.add(it)

func test_enchanting_a_weapon() -> void:
	var h := _hero(&"knight", 20)
	h.inventory.gold = 5000
	_stock(h, {&"ember_core": 20, &"arcane_dust": 30, &"wisp_mote": 10, &"champion_essence": 3})
	var w := DB.make_item(&"iron_longsword", BH.Rarity.ADVANCED, 10, 11)
	h.inventory.add(w)
	eq(WeaponUpgrades.check(h, w, WeaponUpgrades.ENCHANT, &"flame", &"forge"), "Needs an Alchemy Table", "an enchantment needs the alchemy table")
	eq(WeaponUpgrades.check(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy"), "", "the alchemy table is enough")
	var before_dmg := w.damage_range()
	var gold0 := h.inventory.gold
	var r := WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy")
	ok(r.ok, "flame etching applies")
	eq(w.enchant, &"flame", "the weapon carries the rune")
	eq(w.enchant_rank, 1, "rank I")
	ok(h.inventory.gold < gold0, "the fee was paid")
	eq(w.weapon_element(), Elements.FIRE, "part of the damage is fire now")
	near(w.weapon_element_share(), 0.2, 0.0001, "20% at rank I")
	ok(w.modifiers().any(func(m): return m.stat == &"added_fire"), "it adds fire damage")
	eq(w.damage_range(), before_dmg, "an enchantment does not change the weapon's own damage")
	ok(w.display_name().find("+") < 0, "enchantments do not add a +N tag")
	# ranks II and III, then the top
	ok(WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy").ok, "rank II")
	ok(WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy").ok, "rank III")
	eq(w.enchant_rank, 3, "rank III")
	near(w.weapon_element_share(), 0.4, 0.0001, "40% at rank III")
	ok(not WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy").ok, "there is no rank IV")
	# a different rune starts over
	_stock(h, {&"frost_crystal": 10})
	ok(WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"frost", &"alchemy").ok, "frost etching replaces it")
	eq(w.enchant, &"frost", "now frost")
	eq(w.enchant_rank, 1, "starting over at rank I")
	eq(w.weapon_element(), Elements.ICE, "ice replaces the fire")
	done()

func test_fore_tech_refits_a_weapon() -> void:
	var h := _hero(&"knight", 20)
	h.inventory.gold = 9000
	_stock(h, {&"iron_shard": 90, &"steel_ingot": 20, &"orc_tusk": 10, &"ogre_sinew": 4, &"rune_plate": 4, &"champion_essence": 3})
	var w := DB.make_item(&"iron_longsword", BH.Rarity.ADVANCED, 10, 11)
	h.inventory.add(w)
	eq(WeaponUpgrades.check(h, w, WeaponUpgrades.FORETECH, &"whet", &"alchemy"), "Needs a Forge", "Fore-Tech needs the forge")
	var d0 := w.damage_range()
	var name0 := w.display_name()
	for rank in range(1, 6):
		var r := WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"whet", &"forge")
		ok(r.ok, "Fore-Tech rank +%d applies (%s)" % [rank, r.get("error", "")])
		eq(w.foretech_rank, rank, "rank +%d" % rank)
	ok(w.display_name().ends_with("+5"), "the name shows +5 (%s)" % w.display_name())
	ok(w.display_name().begins_with(name0), "the old name is kept")
	near(w.damage_range().y / d0.y, (1.0 + w.quality + 0.10) / (1.0 + w.quality), 0.0005, "tempering adds 2% weapon damage per rank")
	ok(w.modifiers().any(func(m): return m.stat == &"phys_damage"), "the refit adds its own bonus")
	ok(not WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"whet", &"forge").ok, "+5 is the top")
	# it stacks with an enchantment
	_stock(h, {&"ember_core": 4, &"arcane_dust": 8})
	ok(WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy").ok, "an enchantment can be added on top")
	eq(w.foretech_rank, 5, "the refit is kept")
	# a new refit starts over
	ok(WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"serrate", &"forge").ok, "another refit replaces the first")
	eq(w.foretech, &"serrate", "now serrated")
	eq(w.foretech_rank, 1, "back to +1")
	done()

func test_upgrade_refusals_change_nothing() -> void:
	var h := _hero(&"knight", 3)
	h.inventory.gold = 5
	var w := DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 1, 4)
	h.inventory.add(w)
	var armor := DB.make_item(&"iron_hauberk", BH.Rarity.COMMON, 1, 4)
	h.inventory.add(armor)
	var gold := h.inventory.gold
	ok(not WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy").ok, "level 3 cannot etch a rune (level 4 needed)")
	ok(not WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"whet", &"forge").ok, "no materials, no refit")
	ok(not WeaponUpgrades.apply(h, armor, WeaponUpgrades.FORETECH, &"whet", &"forge").ok, "armor is not a weapon")
	ok(not WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"nonsense", &"forge").ok, "an unknown refit is refused")
	eq(h.inventory.gold, gold, "nothing was charged")
	ok(not w.is_upgraded(), "nothing changed on the weapon")
	done()

func test_upgraded_weapons_save_and_fight() -> void:
	var h := _hero(&"knight", 20)
	h.inventory.gold = 9000
	_stock(h, {&"iron_shard": 30, &"steel_ingot": 6, &"ember_core": 6, &"arcane_dust": 12, &"orc_tusk": 4})
	var w := DB.make_item(&"iron_longsword", BH.Rarity.ADVANCED, 10, 11)
	h.inventory.add(w)
	WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy")
	WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"whet", &"forge")
	WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"whet", &"forge")
	var c := w.clone()
	eq(c.enchant, &"flame", "the enchantment survives a save")
	eq(c.foretech_rank, 2, "the refit survives a save")
	eq(c.display_name(), w.display_name(), "same name")
	ok(c.base_value() > DB.make_item(&"iron_longsword", BH.Rarity.ADVANCED, 10, 11).base_value(), "upgrades make it worth more")
	# equipped: the hero's loadout deals the new element
	ok(h.equip_from_inventory(w) == "", "the sword is equipped")
	var lo := h.compute_stats().loadout
	eq(lo.main_element, Elements.FIRE, "the hero's blade now cuts with fire")
	near(lo.main_elem_share, 0.2, 0.0001, "20% of it")
	var plain := _hero(&"knight", 20)
	var w2 := DB.make_item(&"iron_longsword", BH.Rarity.ADVANCED, 10, 11)
	plain.inventory.add(w2)
	plain.equip_from_inventory(w2)
	ok(h.compute_stats().get_stat(&"phys_damage") > plain.compute_stats().get_stat(&"phys_damage"), "Fore-Tech raised Physical Damage")
	# an old save (no keys) still loads
	var d := w2.to_dict()
	ok(not d.has("ench") and not d.has("tech"), "plain weapons save no upgrade keys")
	ok(not ItemInstance.from_dict(d).is_upgraded(), "and load as plain")
	# armor never keeps an upgrade key
	var junk := DB.make_item(&"iron_hauberk", BH.Rarity.COMMON, 1, 4).to_dict()
	junk["ench"] = ["flame", 3]
	ok(not ItemInstance.from_dict(junk).is_upgraded(), "armor ignores a stray upgrade key")
	done()

func test_upgrade_data_is_sound() -> void:
	for id in DataUpgrades.enchant_ids():
		var d := DataUpgrades.enchant(id)
		ok(d.share.size() == 3, "%s has a share for each rank" % id)
		ok(DB.item_base(d.mat) != null, "%s uses a real material (%s)" % [id, d.mat])
		for r in range(1, 4):
			ok(not DataUpgrades.enchant_mods(id, r).is_empty(), "%s rank %d has effects" % [id, r])
			for inp in DataUpgrades.enchant_cost(id, r).inputs:
				ok(DB.item_base(inp[0]) != null, "%s rank %d cost item %s exists" % [id, r, inp[0]])
		ok(DataUpgrades.enchant_share(id, 3) > DataUpgrades.enchant_share(id, 1), "%s grows" % id)
	for id in DataUpgrades.tech_ids():
		for r in range(1, 6):
			ok(not DataUpgrades.tech_mods(id, r).is_empty(), "%s +%d has effects" % [id, r])
			for inp in DataUpgrades.tech_cost(r).inputs:
				ok(DB.item_base(inp[0]) != null, "+%d cost item %s exists" % [r, inp[0]])
		var m1: float = DataUpgrades.tech_mods(id, 1)[0].value
		var m5: float = DataUpgrades.tech_mods(id, 5)[0].value
		ok(absf(m5) > absf(m1), "%s grows with rank" % id)
	done()

# ---- the hero's own guild name and banner ----------------------------------------------------------------------------

func test_guild_alias_rules() -> void:
	eq(GuildRules.clean_alias("  The   Lemon  Legion  "), "The Lemon Legion", "spaces are tidied")
	eq(GuildRules.clean_alias("[b]Bold[/b]"), "bBold/b", "brackets are dropped so text cannot be styled")
	eq(GuildRules.clean_alias("a".repeat(80)).length(), GuildRules.ALIAS_MAX, "the name is capped")
	eq(GuildRules.clean_alias("line\nbreak\t!"), "linebreak!", "control characters are dropped")
	var h := _hero()
	ok(GuildRules.set_alias(h, "Nope") != "", "no guild, no name")
	h.inventory.gold = 500
	ok(GuildRules.join(h, &"swordfin") == "", "join the Swordfin Company")
	eq(GuildRules.display_name(h), "The Swordfin Company", "the guild's own name by default")
	eq(GuildRules.set_alias(h, "Lemon Legion"), "", "a member may name the guild")
	eq(GuildRules.display_name(h), "Lemon Legion", "the new name shows")
	eq(GuildRules.set_alias(h, "Second Thoughts"), "", "and rename it again, any time")
	eq(GuildRules.display_name(h), "Second Thoughts", "renamed")
	GuildRules.set_alias(h, "")
	eq(GuildRules.display_name(h), "The Swordfin Company", "an empty name goes back to the guild's own")
	GuildRules.set_alias(h, "Lemon Legion")
	# survives a save; an old save has none
	var h2 := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(h2.guild_alias, "Lemon Legion", "the name is saved")
	var old := h.to_dict()
	old.erase("guild_alias")
	old.erase("guild_banner")
	eq(HeroData.from_dict(old).guild_alias, "", "an old save loads with the guild's own name")
	done()

func test_guild_banner_upload() -> void:
	var h := _hero()
	h.inventory.gold = 500
	GuildRules.join(h, &"lantern")
	var img := Image.create(640, 400, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.9, 0.2, 0.2, 1.0))
	for x in range(200, 440):
		for y in range(100, 300):
			img.set_pixel(x, y, Color(0.1, 0.4, 0.9, 1.0))
	eq(GuildRules.set_banner(h, img), "", "a picture becomes the banner")
	ok(not h.guild_banner.is_empty() and h.guild_banner.size() < GuildRules.BANNER_MAX_BYTES, "stored as a small JPEG (%d bytes)" % h.guild_banner.size())
	var t := GuildRules.banner_texture(h)
	ok(t != null, "and drawn from it")
	if t:
		eq(t.get_width(), GuildRules.BANNER_W, "banner width")
		eq(t.get_height(), GuildRules.BANNER_H, "banner height")
		var px := t.get_image().get_pixel(GuildRules.BANNER_W / 2, GuildRules.BANNER_H / 2)
		ok(px.b > px.r, "the middle of the picture is the blue square (centre-cropped)")
	var h2 := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	ok(GuildRules.banner_texture(h2) != null, "the banner is saved with the hero")
	GuildRules.clear_banner(h)
	ok(h.guild_banner.is_empty(), "the picture can be removed")
	ok(GuildRules.banner_or_default(h) != null, "the guild's own banner flies again")
	ok(GuildRules.set_banner(_hero(), img) != "", "no guild, no banner")
	ok(GuildRules.set_banner(h, Image.new()) != "", "an empty picture is refused")
	ok(GuildRules.load_banner_bytes("not base64 !!").is_empty(), "garbage in a save is dropped")
	var pic := GuildCustomWindow.picture_from_bytes(img.save_png_to_buffer(), "jpg")
	ok(pic != null, "a picture with the wrong extension is still read")
	done()

# ---- the Quake Team --------------------------------------------------------------------------------------------------

func test_quake_team_cheat_calls_up_to_three() -> void:
	ok(Cheats.is_code("quake team"), "quake team is a cheat code")
	ok(Cheats.is_code("  Quake Team "), "and it ignores case and spaces")
	var h := _hero(&"knight", 12)
	var pl := Node3D.new()
	host.add_child(pl)
	var classes := []
	for i in 3:
		var line := Cheats.apply("quake team", h, pl)
		ok(line.begins_with("Cheat: Quake Team:"), "call %d: %s" % [i + 1, line])
		classes.append((h.quake_team[i] as QuakeMate).class_id())
	eq(h.quake_team.size(), 3, "three allies")
	eq(classes.size(), 3, "three classes listed")
	ok(not classes.has(&"knight"), "no ally duplicates the hero's own class (%s)" % [classes])
	var seen := {}
	for c in classes:
		seen[c] = true
	eq(seen.size(), 3, "each ally is a different class")
	var line4 := Cheats.apply("quake team", h, pl)
	ok(line4.find("full") >= 0, "a fourth is refused: %s" % line4)
	eq(h.quake_team.size(), 3, "still three")
	for m in h.quake_team:
		var mate := m as QuakeMate
		eq(mate.level(), 12, "%s is level 12 like the hero" % mate.display_name())
		ok(mate.hero.equipment.get_item(&"main_weapon") != null, "%s carries a weapon" % mate.display_name())
		ok(mate.tdata.skills.size() >= 2, "%s knows class skills" % mate.display_name())
		ok(mate.hero.progress.free_points == 0, "%s spent their attribute points" % mate.display_name())
		ok(mate.hero.compute_stats().get_stat(&"max_hp") > 100.0, "%s has real stats" % mate.display_name())
	var names := {}
	for m in h.quake_team:
		names[(m as QuakeMate).display_name()] = true
	eq(names.size(), 3, "three different names")
	pl.free()
	done()

func test_quake_team_saves_and_old_saves_load() -> void:
	var h := _hero(&"mage", 9)
	var pl := Node3D.new()
	host.add_child(pl)
	QuakeTeam.summon(h, pl)
	QuakeTeam.summon(h, pl)
	var mate: QuakeMate = h.quake_team[0]
	mate.hero.inventory.gold = 1234
	var d: Dictionary = JSON.parse_string(JSON.stringify(h.to_dict()))
	var h2 := HeroData.from_dict(d)
	eq(h2.quake_team.size(), 2, "both allies come back")
	var m2: QuakeMate = h2.quake_team[0]
	eq(m2.display_name(), mate.display_name(), "same name")
	eq(m2.class_id(), mate.class_id(), "same class")
	eq(m2.hero.inventory.gold, 1234, "same gold")
	eq(m2.level(), mate.level(), "same level")
	eq(m2.uid, mate.uid, "same id")
	for slot in [&"main_weapon", &"armor", &"helm"]:
		var a := mate.hero.equipment.get_item(slot)
		var b := m2.hero.equipment.get_item(slot)
		eq(a.base.id if a else &"", b.base.id if b else &"", "same %s" % slot)
	var old := h.to_dict()
	old.erase("quake_team")
	eq(HeroData.from_dict(old).quake_team.size(), 0, "a save from before the Quake Team loads with none")
	old["quake_team"] = [{"nonsense": true}, 5, {"hero": {"class": "nobody"}}]
	eq(HeroData.from_dict(old).quake_team.size(), 0, "malformed allies are dropped")
	pl.free()
	done()

func test_quake_team_is_single_player_only() -> void:
	var was := Net.mode
	var h := _hero()
	var pl := Node3D.new()
	host.add_child(pl)
	Net.mode = Net.Mode.HOST
	var r := QuakeTeam.summon(h, pl)
	Net.mode = was
	ok(not r.ok and String(r.text).find("Single Player") >= 0, "not in multiplayer: %s" % r.text)
	eq(h.quake_team.size(), 0, "nobody was called")
	pl.free()
	done()

func test_allies_shop_for_the_best_gear() -> void:
	var h := _hero(&"knight", 14)
	var pl := Node3D.new()
	host.add_child(pl)
	QuakeTeam.summon(h, pl)
	var mate: QuakeMate = h.quake_team[0]
	var before := QuakeBrain.rating(mate.hero)
	ok(before > 0.0, "a starting rating exists (%.1f)" % before)
	mate.hero.inventory.gold = 6000
	var row := DataTownRows.row(&"sanctuary")
	var bought := 0
	for s in row.stands:
		if s.kind == DataTownRows.SHOP:
			var res := QuakeBrain.visit_stand(mate, s)
			bought += (res.msgs as Array).size()
	var after := QuakeBrain.rating(mate.hero)
	ok(after >= before, "shopping never makes an ally weaker (%.1f -> %.1f)" % [before, after])
	ok(after > before * 1.05, "with 6000 gold they got clearly stronger (%.1f -> %.1f, %d purchases)" % [before, after, bought])
	ok(mate.hero.inventory.gold < 6000, "they paid")
	# what they wear suits their class
	for slot in [&"main_weapon", &"armor", &"helm"]:
		var it := mate.hero.equipment.get_item(slot)
		ok(it == null or QuakeBrain.suits(mate.hero, it), "%s is class gear (%s)" % [slot, it.display_name() if it else "-"])
	# draughts
	ok(QuakeBrain._potion_count(mate.hero, QuakeBrain.HEAL_IDS) >= 4, "they keep health draughts (%d)" % QuakeBrain._potion_count(mate.hero, QuakeBrain.HEAL_IDS))
	pl.free()
	done()

func test_allies_do_not_overspend_or_buy_junk() -> void:
	var h := _hero(&"ranger", 10)
	var pl := Node3D.new()
	host.add_child(pl)
	QuakeTeam.summon(h, pl)
	var mate: QuakeMate = h.quake_team[0]
	mate.hero.inventory.gold = 30
	var before := QuakeBrain.rating(mate.hero)
	for s in DataTownRows.row(&"sanctuary").stands:
		if s.kind == DataTownRows.SHOP:
			QuakeBrain.visit_stand(mate, s)
	ok(mate.hero.inventory.gold >= 0, "gold never goes negative (%d)" % mate.hero.inventory.gold)
	ok(QuakeBrain.rating(mate.hero) >= before, "still no weaker")
	# equip_best wears the better of two swords from the bag
	var m := mate.hero
	var weak := DB.make_item(&"ashwood_staff", BH.Rarity.BASIC, 3, 1)
	var strong := DB.make_item(&"ashwood_staff", BH.Rarity.ELITE, 20, 2)
	m.equipment.slots[&"main_weapon"] = null
	m.inventory.add(weak)
	m.inventory.add(strong)
	m.progress.level = 30
	QuakeBrain.equip_best(m)
	var worn := m.equipment.get_item(&"main_weapon")
	ok(worn != null and worn.rarity >= weak.rarity, "the better staff is in hand (%s)" % (worn.display_name() if worn else "nothing"))
	pl.free()
	done()

func test_allies_bind_a_tempo() -> void:
	var h := _hero(&"knight", 14)
	var pl := Node3D.new()
	host.add_child(pl)
	QuakeTeam.summon(h, pl)
	var mate: QuakeMate = h.quake_team[0]
	mate.hero.inventory.gold = 5000
	var shrine := {}
	for s in DataTownRows.row(&"sanctuary").stands:
		if s.kind == DataTownRows.SHRINE:
			shrine = s
	ok(not shrine.is_empty(), "Malasugue has a Tempo shrine")
	var res := QuakeBrain.visit_stand(mate, shrine)
	ok(res.hired != null, "with the gold they bind a Tempo")
	eq(mate.hero.tempos.size(), 1, "one Tempo is theirs")
	ok(mate.hero.inventory.gold < 5000, "it cost gold")
	var again := QuakeBrain.visit_stand(mate, shrine)
	ok(again.hired == null and mate.hero.tempos.size() == 1, "one is enough")
	ok((mate.hero.tempos[0] as TempoData).uid >= mate.uid * 1000, "its id cannot collide with the leader's Tempos (%d)" % (mate.hero.tempos[0] as TempoData).uid)
	pl.free()
	done()

func test_allies_appear_follow_and_heal() -> void:
	await _begin(&"sanctuary")
	Game.hero.progress.level = 8
	var r := QuakeTeam.summon(Game.hero, _player)
	ok(r.ok, "summoned in the world")
	var a: QuakeAlly = r.actor
	ok(a != null and is_instance_valid(a), "an ally stands beside the player")
	if a == null:
		_end()
		done()
		return
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	ok(a.is_in_group(&"quake_ally") and a.is_in_group(&"tempo") and a.is_in_group(&"ally"), "it counts as a friendly companion")
	ok(a.stats != null and a.stats.loadout.main_type != null, "it has real stats and a weapon")
	eq(a.level, 8, "level 8")
	ok(a.hp > 0.0 and a.alive, "alive")
	ok(a.max_hp() > 150.0, "with a real hero's health (%d)" % roundi(a.max_hp()))
	# it follows: move the player a long way and let it come (a shopping trip is not due)
	a.mate.shop_gold = 999999
	a.mate.shop_level = 99
	a.mate.shop_map = &"sanctuary"
	_player.global_position += Vector3(0, 0, -8.0)
	for i in 240:
		await host.get_tree().physics_frame
	var d := Vector2(a.global_position.x - _player.global_position.x, a.global_position.z - _player.global_position.z).length()
	ok(d < 9.0, "it followed (%.1f m away)" % d)
	# it drinks a draught when hurt
	a.hp = a.max_hp() * 0.3
	var potions_before := a.hero.inventory.count_of(&"health_potion")
	ok(potions_before > 0, "it carries draughts (%d)" % potions_before)
	for i in 30:
		await host.get_tree().physics_frame
	ok(a.hero.inventory.count_of(&"health_potion") < potions_before, "it drank one")
	# a grievous wound makes the draught worth less
	a.hp = a.max_hp() * 0.3
	a.status.apply(&"grievous")
	a.status.apply(&"grievous")
	var f0 := a.hp
	a.heal(100.0, false)
	near(a.hp - f0, 50.0, 0.5, "healing on a wounded ally is halved")
	# the map reload brings it back
	var mate := a.mate
	Game.hero.quake_team[0] = mate
	_end()
	done()

func test_allies_come_back_after_a_map_change() -> void:
	await _begin(&"sanctuary")
	Game.hero.progress.level = 5
	QuakeTeam.summon(Game.hero, _player)
	QuakeTeam.summon(Game.hero, _player)
	await host.get_tree().physics_frame
	eq(QuakeTeam.actors().size(), 2, "two allies in Malasugue")
	Game.load_map(&"olivar", &"start")
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	eq(QuakeTeam.actors().size(), 2, "and two in Olivar")
	for a in QuakeTeam.actors():
		ok((a as QuakeAlly).mate in Game.hero.quake_team, "%s is on the team" % (a as QuakeAlly).mate.display_name())
	# the leader levels: the team catches up
	Game.hero.progress.add_xp(XpCurve.total_xp_for_level(9) - Game.hero.progress.total_xp)
	for m in Game.hero.quake_team:
		eq((m as QuakeMate).level(), 9, "the ally caught up to level 9")
	_end()
	done()

func test_allies_share_the_gold_of_the_fight() -> void:
	var h := _hero(&"knight", 6)
	var pl := Node3D.new()
	host.add_child(pl)
	QuakeTeam.summon(h, pl)
	var before := (h.quake_team[0] as QuakeMate).hero.inventory.gold
	var saved_hero := Game.hero
	var saved_player = Game.player
	Game.hero = h
	Game.player = pl
	var e := Enemy.new().setup(DB.enemy(&"hollow_soldier"), 6)
	host.add_child(e)
	QuakeTeam._on_actor_died(e, null)
	Game.hero = saved_hero
	Game.player = saved_player
	ok((h.quake_team[0] as QuakeMate).hero.inventory.gold > before, "a kill earns the ally some gold")
	e.free()
	pl.free()
	done()

# ---- trade rows in every town ---------------------------------------------------------------------------------------

func test_every_merchant_stands_on_the_trade_row() -> void:
	for map_id in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		var row := DataTownRows.row(map_id)
		ok(not row.is_empty(), "%s has a trade row" % map_id)
		var stations := {}
		var shops := 0
		for s in row.stands:
			ok(String(s.title) != "" and String(s.sub) != "", "%s: stand %s is signed" % [map_id, s.id])
			if s.kind == DataTownRows.SHOP:
				shops += 1
				var npc := DB.npc(s.npc)
				ok(npc != null and npc.shop != &"", "%s: %s runs a shop" % [map_id, s.npc])
				if npc:
					eq(npc.map, map_id, "%s is in %s" % [s.npc, map_id])
					var want := DataTownRows.npc_spot(s.npc)
					near(npc.position.x, want.position.x, 0.01, "%s stands beside the stall (x)" % s.npc)
					near(npc.position.z, want.position.z, 0.01, "%s stands beside the stall (z)" % s.npc)
					ok(Vector2(npc.position.x - s.pos.x, npc.position.z - s.pos.z).length() < 3.0, "%s is at their stall" % s.npc)
			if s.has("station"):   # a station stand, or a smithy that keeps the forge (bh-018)
				stations[s.station] = true
		for st in [&"forge", &"alchemy", &"workbench"]:
			ok(stations.has(st), "%s: the %s is on the row" % [map_id, st])
		ok(shops >= 2, "%s: %d shops on the row" % [map_id, shops])
	# every shop keeper of every town is on a row
	for npc in DB.npcs.values():
		if npc.shop != &"" and npc.map in [&"sanctuary", &"olivar", &"wyman_outpost"]:
			ok(not DataTownRows.stand_of_npc(npc.id).is_empty(), "%s (%s) has a stand" % [npc.id, npc.shop])
	# the Tempo-Caller too
	ok(not DataTownRows.stand_of_npc(&"veyra").is_empty(), "Veyra keeps a stand on Merchant Row")
	done()

func test_town_rows_build_in_the_world() -> void:
	for map_id in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		await _begin(map_id)
		var map := Game.current_map
		var row := DataTownRows.row(map_id)
		# bh-018: no sign-poles; every stand except the shrine is its own model
		var stands := map.find_children("Stand_*", "Node3D", true, false).size()
		ok(stands >= row.stands.size() - 1, "%s: a stand for every shop and station (%d)" % [map_id, stands])
		var stations := {}
		for n in get_stations(map):
			stations[n.station] = true
		for st in [&"forge", &"alchemy", &"workbench"]:
			ok(stations.has(st), "%s: a %s station stands in the world" % [map_id, st])
		var npcs := 0
		for n in host.get_tree().get_nodes_in_group(&"npc"):
			if n is Npc and (n as Npc).def.shop != &"":
				npcs += 1
				var st := DataTownRows.stand_of_npc((n as Npc).def.id)
				ok(not st.is_empty(), "%s stands on a row" % (n as Npc).def.id)
				if not st.is_empty():
					var loc: Vector3 = map.to_local((n as Npc).global_position)
					ok(Vector2(loc.x - st.pos.x, loc.z - st.pos.z).length() < 3.2, "%s is beside their stall (%.1f m off)" % [(n as Npc).def.id, Vector2(loc.x - st.pos.x, loc.z - st.pos.z).length()])
		ok(npcs >= 2, "%s: %d merchants in the world" % [map_id, npcs])
		_end()
	done()

func get_stations(map: Node) -> Array:
	return map.find_children("Station_*", "CraftingStation", true, false)

func test_allies_walk_the_row_and_shop() -> void:
	await _begin(&"sanctuary")
	Game.hero.progress.level = 12
	var r := QuakeTeam.summon(Game.hero, _player)
	var a: QuakeAlly = r.actor
	ok(a != null, "summoned")
	if a == null:
		_end()
		done()
		return
	a.mate.hero.inventory.gold = 4000
	var before := QuakeBrain.rating(a.mate.hero)
	var trips := [0]
	a.shopped.connect(func(_m: Array) -> void: trips[0] += 1)
	# the leader waits at the head of Merchant Row; the ally goes to the stands on its own
	_player.global_position = Game.current_map.to_global(Vector3(14.8, 0.3, 17.0))
	var frames := 0
	while frames < 3600 and a.mate.shop_map != &"sanctuary":
		await host.get_tree().physics_frame
		frames += 1
	ok(a.mate.shop_map == &"sanctuary", "the ally finished its round of the stands (%d frames)" % frames)
	ok(a.mate.hero.inventory.gold < 4000, "and spent gold (%d left)" % a.mate.hero.inventory.gold)
	ok(QuakeBrain.rating(a.mate.hero) >= before, "without getting weaker")
	ok(QuakeBrain._potion_count(a.mate.hero, QuakeBrain.HEAL_IDS) >= 4, "and keeps draughts in the bag")
	ok(not QuakeBrain.wants_trip(a.mate, &"sanctuary"), "it does not go again straight away")
	_end()
	done()
