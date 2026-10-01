extends TestCase
## bh-029: Zarael Island — the ship at Wyman after Kethrax (old saves included), Agdao and Terax, the Act IV quest chain,
## the three Vaults, the thirty new monsters, the routes and the island's maps. Contract: work/lemondev/bh-029/contract.md.

func _init() -> void:
	strict = true

func _hero(name := "Islander") -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), name)
	h.init_new()
	return h

func _flags(h: HeroData, flags: Array) -> void:
	for f in flags:
		h.world_flags[StringName(f)] = true

const BEFORE_ZARAEL := ["mq_maelis_orders", "south_gate_open", "mq_shard_taken", "mq_three_told", "mq_marsh_gate_open"]

# ---- the ship and the quest chain -------------------------------------------------------------------------------

func test_ship_waits_only_after_kethrax() -> void:
	var h := _hero()
	_flags(h, BEFORE_ZARAEL)
	ok(not DataZarael.ship_ready(h), "no ship while Kethrax lives")
	ok(not NpcDirectory.is_present(DB.npc(&"ilsa"), h), "the captain is not at Wyman yet")
	h.world_flags[&"boss_kethrax_defeated"] = true
	ok(DataZarael.ship_ready(h), "the ship comes when Kethrax falls")
	ok(NpcDirectory.is_present(DB.npc(&"ilsa"), h), "Captain Ilsa waits at the Marsh Jetty")
	eq(StringName(DB.npc(&"ilsa").map), &"wyman_outpost", "her post is Wyman Outpost")
	ok(NpcDirectory.is_present(DB.npc(&"ilsa_agdao"), h), "and she sails back from Agdao's pier")
	done()

func test_old_save_with_kethrax_dead_gets_the_ship_at_once() -> void:
	# a save from before bh-029 that already killed Kethrax and finished Act III: none of the new flags exist
	var h := _hero("Veteran")
	_flags(h, BEFORE_ZARAEL + ["boss_kethrax_defeated", "mq_kethrax_reported", "catacombs_ritual_seen", "temple_seal_broken", "boss_warden_defeated"])
	h.mark_dialogue_visited(&"maelis", "warden_fallen")
	h.mark_dialogue_visited(&"paul_david", "spire")
	h.progress.level = 34
	var back := HeroData.from_dict(h.to_dict())
	ok(back != null, "the old save loads")
	ok(DataZarael.ship_ready(back), "the ship is there immediately")
	eq(Objectives.current(back).id, "zr_ship", "the tracker points at the ship")
	ok(NpcDirectory.is_present(DB.npc(&"ilsa"), back), "the captain is present on load")
	done()

func test_zarael_chain_runs_flag_by_flag() -> void:
	var h := _hero()
	_flags(h, BEFORE_ZARAEL + ["boss_kethrax_defeated", "mq_kethrax_reported", "catacombs_ritual_seen", "temple_seal_broken", "boss_warden_defeated"])
	h.mark_dialogue_visited(&"maelis", "warden_fallen")
	h.mark_dialogue_visited(&"paul_david", "spire")
	var steps := [["zr_ship_sailed", "zr_terax"], ["zr_terax_met", "zr_council"], ["zr_wirekeeper_met", "zr_relays"],
		["zr_relays_cut", "zr_vault_jade"], ["dg_jade_sepulchre_cleared", "zr_vault_obsidian"], ["dg_obsidian_engine_cleared", "zr_vault_vein"],
		["dg_veinworks_cleared", "zr_bridge"], ["boss_deathspan_defeated", "zr_abbot"], ["boss_leash_abbot_defeated", "zr_dawn"],
		["zr_heartwire_restored", "zr_home"]]
	eq(Objectives.current(h).id, "zr_ship", "Act IV starts at the ship")
	for s in steps:
		h.world_flags[StringName(s[0])] = true
		eq(Objectives.current(h).id, s[1], "after %s" % s[0])
	h.mark_dialogue_visited(&"terax", "dawn")
	ok(Objectives.current(h).is_empty(), "Zarael's story is complete")
	for o in Objectives.ZARAEL:
		eq(int(o.act), 4, "%s is Act IV" % o.id)
		ok(String(o.step) != "" and String(o.title) != "", "%s has a title and a step" % o.id)
		ok(not DataIsland.place(String(o.place)).is_empty(), "%s: place %s exists" % [o.id, o.place])
		ok(DB.map_def(StringName(o.map)) != null, "%s: map %s exists" % [o.id, o.map])
		if o.has("npc"):
			ok(DB.npc(StringName(o.npc)) != null, "%s: npc %s exists" % [o.id, o.npc])
	eq(Objectives.act_name(4), "Act IV — Zarael, the Corrupted", "the act has a name")
	done()

func test_act_three_still_leads_on_salmonan_for_a_young_hero() -> void:
	var h := _hero()
	_flags(h, BEFORE_ZARAEL + ["boss_kethrax_defeated", "mq_kethrax_reported"])
	h.progress.level = 8
	eq(Objectives.current(h).id, "forest", "a level-8 hero is sent to the Hollow Warden first")
	h.progress.level = 30
	eq(Objectives.current(h).id, "zr_ship", "a level-30 hero is pointed at the ship")
	h.progress.level = 8
	h.current_map = &"agdao"
	eq(Objectives.current(h).id, "zr_ship", "on Zarael the island's own quest leads")
	done()

func test_relay_and_vault_counters() -> void:
	var h := _hero()
	eq(DataZarael.relays_cut(h), 0, "no relays cut")
	h.world_flags[&"zr_relay_2"] = true
	eq(DataZarael.relays_cut(h), 1, "one relay")
	eq(DataZarael.vaults_cleared(h), 0, "no vaults")
	h.world_flags[DataDungeons.cleared_flag(&"veinworks")] = true
	eq(DataZarael.vaults_cleared(h), 1, "the Veinworks counts as cleared by its dungeon flag")
	for d in DataZarael.VAULT_FLAGS:
		eq(DataZarael.VAULT_FLAGS[d], DataDungeons.cleared_flag(d), "%s's pylon follows its clear flag" % d)
		ok(DataZarael.BR_PYLONS.has(d), "%s has a ward pylon on the bridge" % d)
	eq(DataZarael.wire_state(h), "corrupt", "the Heartwire starts violet")
	h.world_flags[DataZarael.F_RESTORED] = true
	eq(DataZarael.wire_state(h), "restored", "and burns gold once restored")
	done()

func test_new_flags_survive_a_save_round_trip() -> void:
	var h := _hero()
	_flags(h, ["boss_kethrax_defeated", "zr_ship_sailed", "zr_terax_met", "zr_relay_1", "dg_jade_sepulchre_cleared", "zr_heartwire_restored"])
	var back := HeroData.from_dict(h.to_dict())
	for f in ["zr_ship_sailed", "zr_terax_met", "zr_relay_1", "dg_jade_sepulchre_cleared", "zr_heartwire_restored"]:
		ok(back.world_flags.get(StringName(f), false), "%s is saved" % f)
	done()

# ---- dialogue ---------------------------------------------------------------------------------------------------

func test_captain_sails_and_terax_tells_of_aljay() -> void:
	var h := _hero()
	_flags(h, BEFORE_ZARAEL + ["boss_kethrax_defeated"])
	var s := DialogueSession.start(DB.npc(&"ilsa"), h)
	s.begin()
	eq(s.node_id, "offer", "the captain makes her offer")
	# the offer's choices show with its last line
	while not s.finished and s.choices.is_empty() and s.line_index < s.lines.size() - 1:
		s.advance()
	var sail := -1
	var ch: Array = s.choices
	for i in ch.size():
		if String(ch[i].text).begins_with("Set sail"):
			sail = i
	ok(sail >= 0, "she offers to set sail")
	ok((DialogueBox.SERVICES as Array).has(&"sail_zarael") and (DialogueBox.SERVICES as Array).has(&"sail_wyman"), "the voyage services exist")
	var t := DialogueSession.start(DB.npc(&"terax"), h)
	t.begin()
	eq(t.node_id, "welcome", "Terax welcomes a hero who skipped the cutscene")
	var text := " ".join(t.lines)
	ok("Aljay" in text, "Terax names Aljay")
	ok("Bridge of Death" in text, "and the Bridge of Death")
	ok(h.world_flags.get(&"zr_terax_met", false), "the welcome counts as meeting Terax")
	var w := DialogueSession.start(DB.npc(&"wirekeeper"), h)
	w.begin()
	eq(w.node_id, "first", "the Wirekeeper explains the Heartwire")
	ok(h.world_flags.get(&"zr_wirekeeper_met", false), "and sets the relay quest")
	done()

func test_every_zarael_npc_and_shop() -> void:
	for id in [&"ilsa", &"ilsa_agdao", &"terax", &"wirekeeper", &"dorrit", &"brisa", &"ysenne", &"toma", &"caius", &"quillan", &"sorrel"]:
		var n := DB.npc(id)
		ok(n != null, "%s exists" % id)
		if n:
			ok(DB.map_def(n.map) != null, "%s stands on a real map (%s)" % [id, n.map])
			ok(not n.graph.is_empty(), "%s can talk" % id)
			ok(ResourceLoader.exists(n.model), "%s has a model (%s)" % [id, n.model])
	for sh in [&"agdao_arms", &"agdao_remedies"]:
		ok(DB.shops.has(sh), "%s exists" % sh)
	ok(DB.item_base(&"quest_broken_link") != null, "Aljay's broken link exists")
	done()

# ---- maps, routes, dungeons -------------------------------------------------------------------------------------

func test_maps_and_routes() -> void:
	for m in DataZarael.MAPS:
		var d := DB.map_def(m)
		ok(d != null, "%s is registered" % m)
		ok(ResourceLoader.exists(d.builder), "%s has a builder" % m)
		if m != &"agdao":
			ok(d.level_min >= 30 and d.level_max <= 53, "%s levels within 30-53 (%d-%d)" % [m, d.level_min, d.level_max])
	ok(DB.map_def(&"agdao").is_town, "Agdao is a safe town")
	# the route from Wyman's camp to the Heart Citadel crosses the sea and every boundary
	var h := _hero()
	_flags(h, BEFORE_ZARAEL + ["boss_kethrax_defeated", "boss_deathspan_defeated"])
	var plan := RoutePlanner.plan(h, &"wyman_outpost", Vector2(0, 6), "hc_engine", RoutePlanner.Mode.ROADS)
	ok(plan.ok, "a route from Wyman to the Dawn Engine (%s)" % plan.get("reason", ""))
	ok(plan.legs.any(func(l): return l.kind == "ship"), "it takes the ship")
	var locked := _hero()
	_flags(locked, BEFORE_ZARAEL)
	var none := RoutePlanner.plan(locked, &"wyman_outpost", Vector2(0, 6), "agd_pier", RoutePlanner.Mode.ROADS)
	ok(not none.ok, "no route to Zarael before Kethrax falls")
	for r in DataIsland.ROADS:
		if DataZarael.is_zarael_map(StringName(r.map)):
			ok(not DataIsland.place(String(r.a)).is_empty() and not DataIsland.place(String(r.b)).is_empty(), "%s joins real places" % r.id)
	for id in [&"agdao_shrine", &"coil_shrine", &"barrens_shrine"]:
		ok(DataIsland.NETWORK.has(id) and DataIsland.NETWORK_SHRINES.has(id), "%s joins the waypoint network" % id)
	done()

func test_three_vaults() -> void:
	var ids: Array = DataDungeons.order().filter(func(id): return DataDungeons.is_zarael(id))
	eq(ids.size(), 3, "three Vaults")
	for id in ids:
		var d := DataDungeons.get_def(id)
		eq(DataDungeons.floor_count(id), 7, "%s has seven floors" % id)
		for lv in d.levels:
			ok(int(lv[0]) >= 33 and int(lv[1]) <= 53, "%s floor levels within 33-53 (%s)" % [id, lv])
		eq(DataDungeons.min_tier(id), 0, "%s has no tier lock" % id)
		ok(DataZarael.is_zarael_map(DataDungeons.map_id(id, 1)), "%s counts as Zarael" % id)
		eq(StringName(d.surface.map), (DataDungeonsZarael.GATES[id] as Dictionary).map, "%s gate on its map" % id)
		var boss := DB.enemy(d.boss)
		ok(boss != null and boss.archetype == &"boss", "%s lord %s is a boss" % [id, d.boss])
		for key in ["miniboss", "usurper"]:
			ok(DB.enemy(d[key].enemy) != null, "%s %s uses a real monster" % [id, key])
		for pool in d.pools:
			for eid in d.pools[pool]:
				ok(DataEnemiesZarael.ids().has(eid), "%s pool %s: %s is a Zarael monster" % [id, pool, eid])
		ok(DataIsland.all_links().any(func(l): return l.id == "%s_gate" % id), "%s has a route" % id)
	done()

# ---- monsters ---------------------------------------------------------------------------------------------------

func test_thirty_new_monsters() -> void:
	var ids := DataEnemiesZarael.ids()
	ok(ids.size() >= 30, "at least thirty new monsters (%d)" % ids.size())
	var seen := {}
	var bosses := 0
	for id in ids:
		ok(not seen.has(id), "%s is unique" % id)
		seen[id] = true
		var e := DB.enemy(id)
		ok(e != null, "%s is registered" % id)
		if e == null:
			continue
		ok(e.lore != "", "%s has lore" % id)
		ok(not e.attacks.is_empty(), "%s can fight" % id)
		if e.archetype == &"boss":
			bosses += 1
			ok(e.phases.size() >= 3, "%s has three phases" % id)
		for a in e.attacks:
			if a.get("kind", "") == "summon":
				ok(DB.enemy(StringName(a.summon)) != null, "%s summons a real monster" % id)
	eq(bosses, 5, "five Zarael bosses")
	done()

## Every model exists and plays every animation its attacks use (skipped per monster until its GLB is delivered).
func test_monster_models_have_their_clips() -> void:
	var missing := []
	for id in DataEnemiesZarael.ids():
		var e := DB.enemy(id)
		if not ResourceLoader.exists(e.model):
			missing.append(id)
			continue
		if e.body_shape == &"floating":
			continue
		# a GLB delivered but not imported yet loads as null: count it as missing
		var scn := load(e.model) as PackedScene
		if scn == null:
			missing.append(id)
			continue
		var inst := scn.instantiate()
		var ap := inst.find_child("AnimationPlayer", true, false) as AnimationPlayer
		ok(ap != null, "%s has an AnimationPlayer" % id)
		if ap:
			for a in e.attacks:
				var anim := StringName(a.get("anim", &""))
				ok(ap.has_animation(anim) or e.anim_map.has(String(anim)), "%s plays %s" % [id, anim])
		inst.free()
	ok(missing.is_empty(), "every Zarael monster has a model (missing: %s)" % [missing])
	done()
