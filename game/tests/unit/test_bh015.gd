extends TestCase
## bh-015: the HUD column never pushes the minimap off screen; rolled names (Tempos, weapons); 65 new weapons; the
## minimap overhaul (zoom, quest locator, trades); independent multiplayer exploring and summons; save files that
## survive a crash mid-write and old saves that load unchanged.

const SLOT := 98

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _begin(map_id: StringName, spawn: StringName = &"start") -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "Bh015World"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Quester")
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

# ---- names ------------------------------------------------------------------------------------------------------

func test_name_forge() -> void:
	var r := rng(4)
	var seen := {}
	for i in 300:
		var n := NameForge.person(r)
		ok(n.length() >= 4 and n.length() <= 10, "%s is 4-10 letters" % n)
		ok(n[0] == n[0].to_upper() and n.substr(1) == n.substr(1).to_lower(), "%s is capitalised once" % n)
		for w in NameForge.REFUSED:
			ok(not n.to_lower().contains(w), "%s avoids %s" % [n, w])
		seen[n] = true
	ok(seen.size() >= 270, "300 rolls give %d different names" % seen.size())
	var a := NameForge.person(rng(9))
	eq(NameForge.person(rng(9)), a, "the same seed gives the same name")
	var taken := [a]
	var r2 := rng(9)
	ok(NameForge.person(r2, taken) != a, "a taken name is skipped")
	for id in DataTempos.LEGENDS:
		var first := String(DataTempos.LEGENDS[id].name).get_slice(" ", 0).to_lower()
		ok(NameForge.reserved().has(first), "renowned %s is reserved" % first)
	done()

func test_starter_name_is_rolled_and_saved() -> void:
	var names := {}
	for i in 6:
		var h := Game.new_hero(&"knight", "Rolled%d" % i)
		var t := TempoRules.grant_starter(h, 1000 + i)
		names[t.tempo_name] = true
		eq(h.starter_name, t.tempo_name, "the hero remembers %s" % t.tempo_name)
		ok(t.tempo_name != h.hero_name, "the starter is not named after the hero")
	ok(names.size() >= 5, "six new heroes meet %d different starters (was always Tobren)" % names.size())
	var h2 := Game.new_hero(&"mage", "Keeper")
	TempoRules.grant_starter(h2, 77)
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h2.to_dict())))
	eq(back.starter_name, h2.starter_name, "the starter's name survives a save")
	eq(back.tempos[0].tempo_name, h2.starter_name, "and so does the Tempo")
	var old := h2.to_dict()
	old.erase("starter_name")
	eq(HeroData.from_dict(old).starter_name, String(DataTempos.STARTER.name), "a hero from before bh-015 still met Tobren")
	eq(Dialogue.fill("I am **{tempo}**.", h2), "I am **%s**." % h2.starter_name, "the guide quotes the rolled name")
	done()

# ---- weapons ----------------------------------------------------------------------------------------------------

func test_new_weapons() -> void:
	eq(DataItems.ROSTER_BH015.size(), 65, "65 new weapons")
	var per := {}
	for b: ItemBaseDef in DB.item_bases.values():
		if b.is_weapon() and b.unique_name == "" and b.set_id == &"":
			per[b.weapon_type] = int(per.get(b.weapon_type, 0)) + 1
	for t in [&"sword", &"greatsword", &"axe", &"greataxe", &"spear", &"javelin", &"club", &"dagger", &"claw", &"knuckles", &"bow", &"staff", &"wand"]:
		ok(int(per.get(t, 0)) >= 8, "%s has %d weapons" % [t, per.get(t, 0)])
	var top := 0
	for r in DataItems.ROSTER_BH015:
		var b := DB.item_base(r[0])
		ok(b != null, "%s exists" % r[0])
		if b == null:
			continue
		top = maxi(top, b.level_req)
		ok(ResourceLoader.exists(ItemBaseDef.ITEM_MODEL % b.id), "%s has its own model" % b.id)
		ok(ResourceLoader.exists(b.icon), "%s has its icon" % b.id)
		ok(b.damage_min > 0.0 and b.damage_max > b.damage_min, "%s deals %d-%d" % [b.id, b.damage_min, b.damage_max])
		eq(b.class_hint, DataItems._weapon_class(b.weapon_type), "%s is %s gear" % [b.id, b.class_hint])
		if b.weapon_type in [&"staff", &"wand"]:
			eq(b.element_share, 1.0, "%s: the element is the whole blow" % b.id)
	ok(top >= 50, "weapons reach level %d (the cap is %d)" % [top, BH.LEVEL_CAP])
	# a slower weapon of the same level and type hits harder per blow
	var fast := DataItems.roster_damage(&"bow", 30, 1.3)
	var slow := DataItems.roster_damage(&"bow", 30, 0.9)
	ok(slow.y > fast.y, "slow bows hit harder (%s vs %s)" % [slow, fast])
	done()

func test_weapon_names_are_forged() -> void:
	var base := DB.item_base(&"fowling_bow")
	var named := 0
	var names := {}
	for i in 40:
		var it := ItemGenerator.generate(base, 10, BH.Rarity.COMMON, rng(200 + i))
		var n := it.display_name()
		ok(n.contains(base.display_name), "%s still says what it is" % n)
		if it.name_prefix != "" or it.name_suffix != "":
			named += 1
		names[n] = true
		var back := ItemInstance.from_dict(JSON.parse_string(JSON.stringify(it.to_dict())))
		eq(back.display_name(), n, "%s survives a save" % n)
	eq(named, 40, "every Common weapon gets a forged prefix or suffix")
	ok(names.size() >= 25, "40 drops read %d different ways" % names.size())
	var a := ItemGenerator.generate(base, 10, BH.Rarity.BASIC, rng(5))
	var b := ItemGenerator.generate(base, 10, BH.Rarity.BASIC, rng(5))
	eq(a.display_name(), b.display_name(), "the same roll gives the same name")
	var helm := ItemGenerator.generate(DB.item_base(&"iron_helm"), 10, BH.Rarity.COMMON, rng(3))
	eq(helm.display_name(), "Iron Helm", "armour keeps its plain name")
	var starter := ItemGenerator.generate(base, 1, BH.Rarity.BEGINNER, rng(3))
	eq(starter.display_name(), base.display_name, "starter gear stays plain")
	var old := a.to_dict()
	old.erase("np")
	old.erase("ns")
	ok(ItemInstance.from_dict(old) != null, "an item saved before bh-015 still loads")
	done()

# ---- HUD and minimap --------------------------------------------------------------------------------------------

func test_hud_column_stays_on_screen() -> void:
	var hud := Hud.new()
	host.add_child(hud)
	await host.get_tree().process_frame
	eq(hud._top_right.grow_horizontal, Control.GROW_DIRECTION_BEGIN, "the right column grows toward the screen")
	var st: StageTracker = hud._quest_panels[1]
	st.visible = true
	st._title.text = "HOLLOWROOT WARREN — FLOOR I · Stage and a much longer name than any panel could hold"
	for i in 3:
		await host.get_tree().process_frame
	var vw := hud.get_viewport_rect().size.x
	var r: Rect2 = hud._top_right.get_global_rect()
	ok(r.end.x <= vw + 0.5, "the column ends at %.0f inside the %.0f px screen" % [r.end.x, vw])
	ok(r.size.x <= 320.0, "a long title is trimmed, not widening the column (%.0f px)" % r.size.x)
	var mm := hud.minimap_rect()
	ok(mm.end.x <= vw + 0.5, "the minimap stays on screen")
	hud.free()
	done()

func test_minimap_math_and_trades() -> void:
	var mm := MiniMap.new(236.0)
	host.add_child(mm)
	await host.get_tree().process_frame
	ok(mm._disc_r > 236.0 * 0.36, "the map fills the frame's opening (%.1f px)" % mm._disc_r)
	for i in MiniMap.ZOOMS.size():
		mm._zoom_i = i
		mm.radius_m = MiniMap.ZOOMS[i]
		var w := Vector3(7.5, 0, -4.0)
		var q := mm._to_map(w)
		near(mm._to_world(q).x, w.x, 0.01, "zoom %d round-trips x" % i)
		near(mm._to_world(q).z, w.z, 0.01, "zoom %d round-trips z" % i)
		var rim := mm._to_map(Vector3(MiniMap.ZOOMS[i], 0, 0))
		near(rim.x - mm._markers.size.x * 0.5, mm._disc_r, 0.5, "the rim is %d m away at zoom %d" % [int(MiniMap.ZOOMS[i]), i])
	var smith := NpcDef.make(&"t_smith", "Anvil", {"title": "Blacksmith", "shop": &"brannoc_forge"})
	eq(MiniMap._npc_role(smith)[0], "smith", "a blacksmith shows an anvil")
	eq(MiniMap._npc_role(NpcDef.make(&"t_inn", "Bed", {"services": [&"rest"]}))[0], "inn", "an innkeeper shows a bed")
	eq(MiniMap._npc_role(NpcDef.make(&"t_caller", "Call", {"services": [&"tempo_hire"]}))[0], "spirit", "the Tempo-Caller shows a spirit")
	eq(MiniMap._npc_role(NpcDef.make(&"t_shop", "Coin", {"shop": &"tovin_goods"}))[0], "shop", "a merchant shows a coin")
	ok(InputMap.has_action(&"minimap_zoom_in") and InputMap.has_action(&"minimap_zoom_out"), "zoom keys exist")
	mm.free()
	done()

func test_effects_never_bake_into_the_minimap() -> void:
	var l := Label3D.new()
	host.add_child(l)
	eq(l.layers, Perf.FX_LAYER, "floating text lives on the effects layer")
	ok(l.layers & 1 == 0, "which the minimap camera (layer 1) never draws")
	l.free()
	done()

func test_quest_locator() -> void:
	await _begin(&"sanctuary", &"start")
	var q := QuestTarget.new()
	q.resolve()
	eq(q.id, "forest", "a new hero's objective is the forest")
	ok(q.has and not q.final, "in town it points at the way on, not the spot")
	ok(q.path.size() >= 2, "with a trail along the town's roads (%d points)" % q.path.size())
	# the last step: Elder Maelis herself
	for f in [&"catacombs_ritual_seen", &"temple_seal_broken", &"boss_warden_defeated"]:
		Game.hero.world_flags[f] = true
	q.invalidate()
	q.resolve()
	eq(q.id, "after", "after the Warden: back to Maelis")
	var maelis: Node3D = null
	for n in host.get_tree().get_nodes_in_group(&"npc"):
		if n.def.id == &"maelis":
			maelis = n
	ok(maelis != null, "Maelis stands in town")
	if maelis:
		ok(q.final and q.world.distance_to(maelis.global_position) < 0.1, "the marker is on Maelis")
	_end()
	done()

# ---- multiplayer ------------------------------------------------------------------------------------------------

func test_multiplayer_rules_offline() -> void:
	ok(not Net.is_active(), "the suite runs offline")
	ok(Net.may_travel(), "travel is never blocked (everyone explores on their own)")
	ok(not Net.host_on(&"sanctuary"), "offline there is no host's world")
	eq(Net.summon_party(), 0, "nobody to summon offline")
	ok(Net.PROTOCOL >= 4, "a new protocol: older games cannot join a bh-015 game half-way")
	ok(InputMap.has_action(&"summon_party"), "the Summon Party key exists")
	done()

# ---- saves ------------------------------------------------------------------------------------------------------

func test_saves_survive_a_bad_write() -> void:
	SaveSystem.delete_slot(SLOT)
	var h := Game.new_hero(&"knight", "Backup")
	TempoRules.grant_starter(h, 5)
	ok(SaveSystem.save_hero(h, SLOT), "first save")
	h.inventory.gold = 1234
	ok(SaveSystem.save_hero(h, SLOT), "second save")
	var path := SaveSystem.slot_path(SLOT)
	ok(FileAccess.file_exists(path + ".bak"), "the previous save is kept as a backup")
	ok(not FileAccess.file_exists(path + ".tmp"), "no temporary file is left behind")
	eq(int(SaveSystem.read_slot(SLOT).hero.gold), 1234, "the newest save is read")
	# a torn write: the save is garbage
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string("{\"version\": 4, \"hero\": {\"na")
	f.close()
	var d := SaveSystem.read_slot(SLOT)
	eq(String(d.get("hero", {}).get("name", "")), "Backup", "a corrupt slot is restored from its backup")
	var back := SaveSystem.load_hero(SLOT)
	ok(back != null and back.starter_name == h.starter_name, "and loads as the same hero")
	SaveSystem.delete_slot(SLOT)
	ok(not FileAccess.file_exists(path) and not FileAccess.file_exists(path + ".bak"), "deleting a slot removes its backup too")
	eq(SaveSystem.read_slot(SLOT), {}, "a deleted slot stays empty")
	done()

func test_old_saves_load_unchanged() -> void:
	var h := Game.new_hero(&"ranger", "Veteran")
	h.inventory.gold = 321
	var it := ItemGenerator.generate(DB.item_base(&"hunters_bow"), 5, BH.Rarity.BASIC, rng(8))
	h.inventory.add(it)
	var d := SaveSystem.serialize(h)
	eq(int(d.version), SaveSystem.CURRENT_VERSION, "saves keep version %d (new fields are optional)" % SaveSystem.CURRENT_VERSION)
	# strip everything bh-015 added, as a save from the last release would look
	d.hero.erase("starter_name")
	for e in d.hero.inventory:
		if e is Dictionary:
			e.erase("np")
			e.erase("ns")
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(d)).hero)
	ok(back != null, "a bh-014 save loads")
	eq(back.inventory.gold, 321, "gold intact")
	ok(back.inventory.count_of(&"hunters_bow") >= 1, "items intact")
	done()
