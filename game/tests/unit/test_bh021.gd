extends TestCase
## bh-021: the Forsaken Hero story — the new main chain, its conversations, the cutscene engine's skip rules, the
## legends' models and clips, Kethrax and the Weeping Causeway, and old saves picking the story up.

const LEGEND_CLIPS := {
	"aljay": ["cs_aj_kneel", "cs_aj_rise", "cs_aj_point", "cs_aj_clutch", "cs_aj_charge", "cs_aj_chained", "cs_aj_dragged", "cs_aj_stand"],
	"roydo": ["cs_ro_land", "cs_ro_shoulder", "cs_ro_slam", "cs_ro_brace", "cs_ro_fall", "cs_ro_stand"],
	"paul_david": ["cs_pd_idle", "cs_pd_shard", "cs_pd_hand", "cs_pd_gesture", "cs_pd_branded", "cs_pd_reach", "cs_pd_ready", "idle", "interact_talk"],
	"kethrax": ["cs_kx_emerge", "cs_kx_pull", "cs_kx_bind", "cs_kx_kneel", "boss_sweep", "boss_slam", "boss_charge", "boss_roar", "boss_summon", "cast_heavy", "idle", "run", "death"],
}

func _init() -> void:
	strict = true

func _hero(name := "Story") -> HeroData:
	return Game.new_hero(&"knight", name)

func _flags(h: HeroData, ids: Array) -> void:
	for f in ids:
		h.world_flags[StringName(f)] = true

# ---------------------------------------------------------------------------------------------------------------- chain

func test_chain_order() -> void:
	var h := _hero()
	var order := []
	for o in Objectives.CHAIN:
		order.append(o.id)
	eq(order.slice(0, 7), ["awaken", "gate", "wyman", "olivar", "marsh", "kethrax", "report"], "Act I and II in order")
	eq(Objectives.current(h).id, "awaken", "a new hero starts with Maelis")
	var steps := [["mq_maelis_orders", "gate"], ["south_gate_open", "wyman"], ["mq_shard_taken", "olivar"], ["mq_three_told", "marsh"],
		["mq_marsh_gate_open", "kethrax"], ["boss_kethrax_defeated", "report"], ["mq_kethrax_reported", "forest"],
		["catacombs_ritual_seen", "temple"], ["temple_seal_broken", "warden"], ["boss_warden_defeated", "after"]]
	for s in steps:
		h.world_flags[StringName(s[0])] = true
		eq(Objectives.current(h).id, s[1], "after %s" % s[0])
	h.mark_dialogue_visited(&"maelis", "warden_fallen")
	eq(Objectives.current(h).id, "spire", "then the Black Spire with Paul David")
	h.mark_dialogue_visited(&"paul_david", "spire")
	ok(Objectives.current(h).is_empty(), "the story so far is complete")
	for o in Objectives.CHAIN:
		ok(String(o.get("step", "")) != "" and String(o.get("title", "")) != "", "%s has a title and a step" % o.id)
		if o.has("npc"):
			ok(DB.npc(StringName(o.npc)) != null, "%s: npc %s exists" % [o.id, o.npc])
		if String(o.get("place", "")) != "":
			ok(not DataIsland.place(String(o.place)).is_empty(), "%s: place %s exists" % [o.id, o.place])
	done()

func test_old_save_picks_up_the_story() -> void:
	# a hero from before bh-021 who had already beaten the Warden: every new flag missing
	var h := _hero("Veteran")
	_flags(h, ["south_gate_open", "catacombs_ritual_seen", "temple_seal_broken", "boss_warden_defeated"])
	h.mark_dialogue_visited(&"maelis", "warden_fallen")
	var d := h.to_dict()
	var back := HeroData.from_dict(d)
	ok(back != null, "old-style save loads")
	eq(Objectives.current(back).id, "awaken", "the new story starts with Maelis")
	back.world_flags[&"mq_maelis_orders"] = true
	eq(Objectives.current(back).id, "wyman", "the gate is already open, so straight to Wyman")
	done()

# ---------------------------------------------------------------------------------------------------------------- dialogue

func _graph_refs(def: NpcDef) -> void:
	var nodes: Dictionary = def.graph.get("nodes", {})
	for e in def.graph.get("entries", []):
		ok(nodes.has(String(e[1])), "%s entry -> %s" % [def.id, e[1]])
	for id in nodes:
		var n: Dictionary = nodes[id]
		var nxt := String(n.get("next", "end"))
		ok(nxt == "end" or nodes.has(nxt), "%s.%s next %s" % [def.id, id, nxt])
		for c in n.get("choices", []):
			var cn := String(c.get("next", "end"))
			ok(cn == "end" or nodes.has(cn), "%s.%s choice -> %s" % [def.id, id, cn])
			for a in c.get("actions", []):
				if a.has("cutscene"):
					ok(DataCutscenes.make(StringName(a.cutscene)) != null, "%s cutscene %s exists" % [def.id, a.cutscene])
					var r := String(a.get("resume", ""))
					ok(r == "" or nodes.has(r), "%s resume %s exists" % [def.id, r])
		for b in n.get("branch", []):
			ok(nodes.has(String(b[1])), "%s.%s branch -> %s" % [def.id, id, b[1]])

func test_graphs_are_whole() -> void:
	for id in [&"paul_david", &"maelis", &"hald", &"aldric"]:
		var def := DB.npc(id)
		ok(def != null, "%s exists" % id)
		if def:
			_graph_refs(def)
	var pd := DB.npc(&"paul_david")
	eq(pd.map, &"olivar", "Paul David lives in Olivar")
	eq(pd.legend, &"paul_david", "his plate is a legend's plate")
	ok(ResourceLoader.exists(pd.portrait), "portrait rendered from his model")
	ok(ResourceLoader.exists(pd.model), "model exists")
	done()

func _session(def: NpcDef, h: HeroData) -> Array:
	var reqs := []
	var s := DialogueSession.start(def, h)
	s.request.connect(func(k, a) -> void: reqs.append([k, a]))
	s.begin()
	return [s, reqs]

func test_opening_errand_flow() -> void:
	var h := _hero("Errand")
	var r := _session(DB.npc(&"maelis"), h)
	var s: DialogueSession = r[0]
	eq(s.node_id, "orders", "Maelis opens with the errand")
	ok(h.world_flags.get(&"mq_maelis_orders", false), "the errand is given")
	ok(h.inventory.count_of(&"health_potion") >= 3, "and three draughts")
	r = _session(DB.npc(&"hald"), h)
	s = r[0]
	eq(s.node_id, "token", "Hald sees the Elder's token")
	s.advance()
	s.advance()
	s.choose(0)
	ok(h.world_flags.get(&"south_gate_open", false), "the South Gate opens")
	r = _session(DB.npc(&"aldric"), h)
	s = r[0]
	var reqs: Array = r[1]
	eq(s.node_id, "reliquary", "Aldric has the reliquary")
	s.advance()
	s.advance()
	s.choose(0)
	ok(reqs.any(func(q): return q[0] == &"cutscene" and q[1].id == &"shard" and q[1].resume == "shard_after"), "opening it plays the shard cutscene, then resumes")
	var s2 := DialogueSession.start(DB.npc(&"aldric"), h)
	s2.begin("shard_after")
	ok(h.world_flags.get(&"mq_shard_taken", false), "the shard is taken")
	eq(h.inventory.count_of(&"quest_lance_shard"), 1, "the Dusk-Piercer Shard is in the pack")
	# Paul David: the shard -> the tale (no skip-all) -> orders
	r = _session(DB.npc(&"paul_david"), h)
	s = r[0]
	reqs = r[1]
	eq(s.node_id, "shard", "Paul David feels the shard")
	s.advance()
	s.advance()
	s.choose(0)
	ok(reqs.any(func(q): return q[0] == &"cutscene" and q[1].id == &"the_three" and q[1].resume == "after_tale"), "the tale plays and resumes after it")
	s2 = DialogueSession.start(DB.npc(&"paul_david"), h)
	s2.begin("orders")
	ok(h.world_flags.get(&"mq_three_told", false), "his orders set the next step")
	eq(Objectives.current(h).id, "marsh", "back to Aldric for the Marsh Gate")
	r = _session(DB.npc(&"aldric"), h)
	eq((r[0] as DialogueSession).node_id, "marsh_gate", "Aldric opens the Marsh Gate on Paul David's word")
	ok(h.world_flags.get(&"mq_marsh_gate_open", false), "the Marsh Gate is open")
	done()

func test_paul_after_kethrax() -> void:
	var h := _hero("Report")
	_flags(h, ["mq_maelis_orders", "south_gate_open", "mq_shard_taken", "mq_three_told", "mq_marsh_gate_open", "boss_kethrax_defeated"])
	var pts := h.progress.skill_points
	var level := h.progress.level
	var r := _session(DB.npc(&"paul_david"), h)
	eq((r[0] as DialogueSession).node_id, "report", "he feels the chain break")
	ok(h.world_flags.get(&"mq_kethrax_reported", false), "reported")
	eq(h.progress.skill_points, pts + 1 + (h.progress.level - level) * h.cls.skill_points_per_level, "quest point plus earned level-up points")
	eq(Objectives.current(h).id, "forest", "on to the Hollow Warden")
	_flags(h, ["catacombs_ritual_seen", "temple_seal_broken", "boss_warden_defeated"])
	r = _session(DB.npc(&"paul_david"), h)
	eq((r[0] as DialogueSession).node_id, "spire", "the Black Spire")
	done()

# ---------------------------------------------------------------------------------------------------------------- cutscenes

func test_cutscene_data() -> void:
	for id in DataCutscenes.ids():
		var c := DataCutscenes.make(id)
		ok(c != null, "%s builds" % id)
		eq(c.skip_all, id != &"the_three", "%s skip-all rule" % id)
	ok(ResourceLoader.exists("res://assets/audio/music/music_legend.wav"), "the legends' music exists")
	done()

func test_the_three_skips_scene_by_scene_only() -> void:
	var old_hero := Game.hero
	Game.hero = _hero("Viewer")
	var c := DataCutscenes.make(&"the_three")
	var done_calls := [0]
	var cp := CutscenePlayer.play_cutscene(c, func() -> void: done_calls[0] += 1, host)
	ok(cp != null and CutscenePlayer.is_playing(), "the tale plays")
	eq(cp.scenes.size(), 11, "eleven scenes")
	ok(not cp._skip_all_btn.visible, "no Skip all button")
	cp.t = 1.0
	cp.skip_all()
	ok(CutscenePlayer.is_playing(), "Skip all does nothing here")
	eq(cp.index, 0, "still the first scene")
	cp.t = 0.1
	cp.skip_scene()
	eq(cp.index, 0, "a skip in the first 0.35 s is ignored (no double-skips)")
	for i in range(1, 11):
		cp.t = 1.0
		cp.skip_scene()
		eq(cp.index, i, "Skip scene moves exactly one scene (%d)" % i)
		await host.get_tree().process_frame
	ok(Game.in_cutscene, "gameplay is held while it plays")
	cp.t = 1.0
	cp.skip_scene()
	await host.get_tree().process_frame
	ok(not CutscenePlayer.is_playing(), "skipping the last scene ends it")
	eq(done_calls[0], 1, "the dialogue resumes once")
	ok(Game.hero.world_flags.get(&"the_three_seen", false), "finish ran")
	ok(not Game.in_cutscene and not Game.ui_blocking, "gameplay handed back")
	ok(not host.get_tree().root.disable_3d, "the world is drawn again")
	Game.hero = old_hero
	done()

func test_skippable_cutscenes_skip_whole() -> void:
	var old_hero := Game.hero
	Game.hero = _hero("Skipper")
	var cp := CutscenePlayer.play(&"prologue", Callable(), host)
	ok(cp._skip_all_btn.visible, "the prologue offers Skip all")
	cp.skip_all()
	await host.get_tree().process_frame
	ok(not CutscenePlayer.is_playing(), "and ends on it")
	ok(Game.hero.world_flags.get(&"prologue_seen", false), "finish still ran")
	Game.hero = old_hero
	done()

func test_story_director_starts_the_intro() -> void:
	var old_hero := Game.hero
	Game.hero = _hero("Director")
	Game.set_world_flag(&"kethrax_intro_seen")
	ok(CutscenePlayer.is_playing(), "entering the Tollhouse starts the Kethrax intro")
	if CutscenePlayer.active:
		eq(CutscenePlayer.active.cutscene.id, &"kethrax_intro", "the right one")
		CutscenePlayer.active.skip_all()
	await host.get_tree().process_frame
	ok(not CutscenePlayer.is_playing(), "it can be skipped")
	Game.hero = old_hero
	done()

# ---------------------------------------------------------------------------------------------------------------- assets

func _anims(path: String) -> PackedStringArray:
	var out := PackedStringArray()
	var ps := load(path) as PackedScene
	if ps == null:
		return out
	var n := ps.instantiate()
	for ap in n.find_children("*", "AnimationPlayer", true, false):
		for a in (ap as AnimationPlayer).get_animation_list():
			out.append(a)
	n.free()
	return out

func test_legend_models_and_clips() -> void:
	for id in LEGEND_CLIPS:
		var path := "res://assets/characters/%s.glb" % id
		ok(ResourceLoader.exists(path), "%s model" % id)
		var have := _anims(path)
		for c in LEGEND_CLIPS[id]:
			ok(have.has(c), "%s has clip %s" % [id, c])
	for w in ["dusk_piercer", "dusk_piercer_broken", "dusk_piercer_tip", "dawnmaul", "stormwake", "kethrax_mace"]:
		ok(ResourceLoader.exists("res://assets/weapons/legend/%s.glb" % w), "weapon %s" % w)
	for s in ["dragon_scale", "engraved_plate", "forsaken_iron", "chainmail", "leather_worn", "storm_wool", "tyrant_bone"]:
		for k in ["albedo", "normal", "rough"]:
			ok(ResourceLoader.exists("res://assets/textures/legend/%s_%s.png" % [s, k]), "texture %s_%s" % [s, k])
	ok(ResourceLoader.exists(DataLegends.SX_EMBLEM), "Class SX emblem")
	# the legends get real textured materials (box-projected UVs + texture sets)
	var a := CutsceneActor.make("aljay", 1.14)
	host.add_child(a)
	var textured := 0
	for mi in a._meshes:
		for i in mi.mesh.get_surface_count():
			var m := mi.get_surface_override_material(i) as StandardMaterial3D
			if m and m.albedo_texture:
				textured += 1
	ok(textured >= 5, "Aljay's armour is textured (%d surfaces)" % textured)
	a.free()
	done()

func test_legend_data() -> void:
	for id in [&"aljay", &"roydo", &"paul_david"]:
		var L := DataLegends.legend(id)
		eq(L.rank, "SX", "%s is Class SX" % id)
		ok(int(L.level) > 200, "%s is above level 200" % id)
		ok(DataLegends.rank_line(id).begins_with("Class SX · Lv "), "%s plate line" % id)
	eq(DataLegends.legend(&"aljay").epithet, "The Forsaken Hero", "Aljay's epithet")
	eq(DataLegends.legend(&"roydo").epithet, "The Righteous Hammer", "Roydo's epithet")
	var p := LegendPlate.make(&"paul_david", 2.3)
	host.add_child(p)
	ok(p._emblem != null and p._name.text == "Paul David", "the plate shows the SX emblem and his name")
	p.free()
	done()

# ---------------------------------------------------------------------------------------------------------------- boss & map

func test_kethrax_and_the_legion() -> void:
	var k := DB.enemy(&"kethrax")
	ok(k != null, "Kethrax exists")
	eq(k.archetype, &"boss", "a boss")
	eq(k.phases.size(), 3, "three phases")
	ok(ResourceLoader.exists(k.model) and ResourceLoader.exists(k.weapon), "model and chain-mace")
	ok(k.attacks.any(func(a): return a.kind == "tongue"), "his chain drags the hero in")
	ok(k.attacks.any(func(a): return a.kind == "summon" and DB.enemy(StringName(a.summon)) != null), "he calls the Legion")
	for id in [&"forsaken_legionnaire", &"forsaken_chainguard"]:
		var e := DB.enemy(id)
		ok(e != null and ResourceLoader.exists(e.model), "%s" % id)
	ok(k.loot.any(func(l): return l[0] == &"quest_chain_seal"), "drops his chain-seal")
	ok(DB.item_base(&"quest_chain_seal") != null and DB.item_base(&"quest_lance_shard") != null, "quest items exist")
	done()

func test_weeping_causeway_map() -> void:
	var m := Game.build_map(&"weeping_causeway")
	ok(m != null, "the causeway builds")
	if m == null:
		done()
		return
	var boss := []
	for n in m.find_children("*", "Marker3D", true, false):
		if n.is_in_group(&"boss_spawn"):
			boss.append(n)
	eq(boss.size(), 1, "one boss spawn")
	if not boss.is_empty():
		eq(StringName(boss[0].get_meta(&"boss")), &"kethrax", "Kethrax waits there")
		eq(StringName(boss[0].get_meta(&"flag")), &"boss_kethrax_defeated", "and his flag")
	ok(m.find_child("Trigger_kethrax_intro_seen", true, false) != null, "the Tollhouse trigger")
	var exits := m.find_children("*", "MapExit", true, false)
	ok(exits.any(func(e): return e.destination_map == &"wyman_outpost"), "the way back to Wyman")
	m.free()
	var w := Game.build_map(&"wyman_outpost")
	var gate = null
	for e in w.find_children("*", "MapExit", true, false):
		if e.destination_map == &"weeping_causeway":
			gate = e
	ok(gate != null, "Wyman has the Marsh Gate")
	if gate:
		eq(gate.require_flag, &"mq_marsh_gate_open", "barred until Aldric opens it")
	w.free()
	var link := {}
	for l in DataIsland.LINKS:
		if l.id == "marsh_gate_boundary":
			link = l
	eq(String(link.get("flag", "")), "mq_marsh_gate_open", "the atlas knows the gate is barred")
	done()
