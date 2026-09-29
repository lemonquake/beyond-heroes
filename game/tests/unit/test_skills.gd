extends TestCase
## bh-010 skill expansion: every class's skill tree (Knight, Mage, Ranger, Shadowblade) — data integrity (skills,
## passives, auras, synergies, pages, icons), tree reachability, passive/aura math, the Focus and Combo resources,
## save round trips for all four classes, and a live cast of every active skill of every class in a real map.

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
const NEW_BEHAVIORS := [&"melee_arc", &"projectile", &"ground_aoe", &"self_aoe", &"leap", &"blink", &"buff", &"spin",
	&"chain", &"wave", &"dash_strike", &"judgment", &"flurry", &"spiral", &"aura", &"storm", &"sentry", &"orb", &"trap",
	&"vault", &"shadow_step", &"veil", &"mark"]

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _tree() -> SceneTree:
	return host.get_tree()

func _frames(n := 2) -> void:
	for i in n:
		await _tree().physics_frame

func _hero(cls: StringName, lvl := 30) -> HeroData:
	var h := Game.new_hero(cls, "SkillTest")
	if lvl > 1:
		h.progress.add_xp(XpCurve.total_xp_for_level(lvl))
	return h

func _tree_of(cls: StringName) -> TreeDef:
	return DB.tree(DB.class_def(cls).skill_tree_id)

## Rank every node of the hero's skill tree to the cap it had before bh-016 (ignores the point budget: data/behaviour
## tests only). Level 25 everywhere is not a state a hero can reach (its passives alone would make casting free).
func _learn_all(h: HeroData) -> void:
	for n in h.skill_tree.tree.nodes:
		h.skill_tree.ranks[n.id] = int(n.get("base_rank", n.get("max_rank", 1)))
	h._skills_changed()

# ------------------------------------------------------------------------------------------------------------ data

func test_every_class_is_registered() -> void:
	for cls in CLASSES:
		var c := DB.class_def(cls)
		ok(c != null, "%s class exists" % cls)
		if c == null:
			continue
		ok(_tree_of(cls) != null, "%s skill tree %s exists" % [cls, c.skill_tree_id])
		ok(DB.tree(c.talent_tree_id) != null, "%s talent tree %s exists" % [cls, c.talent_tree_id])
		for bid in c.starting_items:
			ok(DB.item_base(bid) != null, "%s starting item %s exists" % [cls, bid])
		for sid in c.starting_skills:
			ok(DB.skill(sid) != null, "%s starting skill %s exists" % [cls, sid])
			ok(_tree_of(cls).node(sid).size() > 0, "%s starting skill %s is in its tree" % [cls, sid])
		ok(c.class_resource_name != "" and c.resource_desc != "", "%s explains its class resource" % cls)
		ok(c.strengths.size() >= 2 and c.weaknesses.size() >= 2, "%s lists strengths and weaknesses" % cls)
	done()

func test_every_node_resolves() -> void:
	for cls in CLASSES:
		var t := _tree_of(cls)
		if t == null:
			continue
		var ids := {}
		for n in t.nodes:
			ok(not ids.has(n.id), "%s: node id %s is unique" % [cls, n.id])
			ids[n.id] = true
			var kind: String = n.get("kind", "skill")
			ok(int(n.get("page", 0)) < t.page_count(), "%s.%s sits on an existing page" % [cls, n.id])
			ok(int(n.get("max_rank", 1)) >= 1, "%s.%s has a max rank" % [cls, n.id])
			for r in n.get("requires", []) + n.get("requires_all", []):
				ok(t.node(r).size() > 0, "%s.%s requirement %s exists" % [cls, n.id, r])
			for syn in n.get("synergies", []):
				ok(t.node(StringName(syn[0])).size() > 0, "%s.%s synergy %s exists" % [cls, n.id, syn[0]])
				ok(float(syn[1]) > 0.0 and float(syn[1]) <= 25.0, "%s.%s synergy %s is sane (%s%%/rank)" % [cls, n.id, syn[0], syn[1]])
			match kind:
				"skill":
					var s := DB.skill(n.get("skill", n.id))
					ok(s != null, "%s.%s skill def exists" % [cls, n.id])
					if s == null:
						continue
					ok(s.class_id == cls, "%s.%s belongs to the class (%s)" % [cls, n.id, s.class_id])
					ok(s.behavior in NEW_BEHAVIORS, "%s.%s behaviour %s is implemented" % [cls, n.id, s.behavior])
					ok(ResourceLoader.exists(s.icon) if s.icon != "" else false, "%s.%s icon %s exists" % [cls, n.id, s.icon])
					for r in [1, int(n.get("max_rank", 1)), int(n.get("max_rank", 1)) + 5]:
						var p := s.resolve(r)
						for k in p:
							if p[k] is float or p[k] is int:
								ok(is_finite(float(p[k])) and float(p[k]) >= 0.0, "%s.%s %s is finite and >= 0 at rank %d" % [cls, n.id, k, r])
						for k in _placeholders(s.description):
							ok(p.has(k), "%s.%s description param {%s} exists at rank %d" % [cls, n.id, k, r])
					ok(s.mana_at(1) >= 0.0 and s.cooldown >= 0.0, "%s.%s cost/cooldown sane" % [cls, n.id])
					if s.is_aura():
						ok(s.aura_kind in [&"offense", &"defense"], "%s.%s aura kind set" % [cls, n.id])
						ok(float(s.resolve(1).get("reserve", 0.0)) > 0.0, "%s.%s aura reserves Mana" % [cls, n.id])
				"passive":
					ok(not (n.get("mods", []).is_empty() and n.get("flags", {}).is_empty()), "%s.%s passive does something" % [cls, n.id])
					for m in n.get("mods", []):
						ok(_known_stat(StringName(m[0])), "%s.%s passive stat %s is a known stat" % [cls, n.id, m[0]])
						ok(m.size() >= 3 and is_finite(float(m[2])), "%s.%s passive mod %s has a base" % [cls, n.id, m[0]])
					var icon := String(n.get("icon", n.id))
					if not icon.begins_with("res://"):
						icon = "res://assets/ui/icons/skills/%s.svg" % icon
					ok(ResourceLoader.exists(icon), "%s.%s passive icon %s exists" % [cls, n.id, icon])
					ok(DataSkillsExt.passive_text(n, 1) != "", "%s.%s passive has text" % [cls, n.id])
				"upgrade":
					ok(DB.skill(n.get("skill", &"")) != null, "%s.%s upgrade targets a skill" % [cls, n.id])
	done()

## Every node can be reached from a root by learning its requirements (points and levels permitting).
func test_every_node_is_reachable() -> void:
	for cls in CLASSES:
		var t := _tree_of(cls)
		if t == null:
			continue
		var h := _hero(cls, 60)
		var pts := 999
		var learned := {}
		var changed := true
		while changed:
			changed = false
			for n in t.nodes:
				if learned.has(n.id):
					continue
				if h.skill_tree.can_rank_up(n.id, pts, 60) == "":
					h.skill_tree.rank_up(n.id, pts, 60)
					learned[n.id] = true
					changed = true
		for n in t.nodes:
			ok(learned.has(n.id), "%s.%s is reachable (%s)" % [cls, n.id, h.skill_tree.can_rank_up(n.id, pts, 60)])
	done()

func test_passives_raise_stats_and_items_raise_passives() -> void:
	var h := _hero(&"knight", 30)
	var before := h.compute_stats().get_stat(&"defense")
	h.skill_tree.ranks[&"iron_skin"] = 1
	h._skills_changed()
	var r1 := h.compute_stats().get_stat(&"defense")
	ok(r1 > before, "Iron Skin rank 1 raises Defense (%.1f -> %.1f)" % [before, r1])
	h.skill_tree.ranks[&"iron_skin"] = 5
	h._skills_changed()
	var r5 := h.compute_stats().get_stat(&"defense")
	ok(r5 > r1, "Iron Skin rank 5 beats rank 1 (%.1f > %.1f)" % [r5, r1])
	var mods := h.skill_tree.passive_modifiers(0)
	var mods2 := h.skill_tree.passive_modifiers(2)
	ok(mods.size() == mods2.size() and mods.size() > 0, "item +skills raise learned passives without adding new ones")
	ok(HeroData.item_skill_levels([StatModifier.flat(&"skill_levels", 9.0)]) == 5, "+skill levels from items are capped at 5")
	done()

func test_synergies_add_damage() -> void:
	var found := false
	for cls in CLASSES:
		var t := _tree_of(cls)
		for n in t.nodes:
			if n.get("synergies", []).is_empty():
				continue
			found = true
			var h := _hero(cls, 30)
			h.skill_tree.ranks[n.id] = 1
			var syn: Array = n.synergies[0]
			h.skill_tree.ranks[StringName(syn[0])] = 0
			var base := float(h.resolved_skill(n.id).get("syn_pct", 0.0))
			h.skill_tree.ranks[StringName(syn[0])] = 3
			var withs := float(h.resolved_skill(n.id).get("syn_pct", 0.0))
			near(withs - base, float(syn[1]) * 3.0, 0.01, "%s.%s: 3 ranks of %s add %s%% x3" % [cls, n.id, syn[0], syn[1]])
			break
	ok(found, "at least one synergy exists")
	done()

func test_focus_and_combo() -> void:
	var f := ClassResource.new(&"focus")
	f.tick(1.0, true, false, true, false)
	ok(f.value > 0.0, "Focus builds while calm at range (%.1f)" % f.value)
	var v := f.value
	f.tick(1.0, true, false, false, true)
	ok(f.value < v, "Focus drains under pressure (%.1f -> %.1f)" % [v, f.value])
	f.value = 70.0
	ok(f.is_steady(), "70 Focus is Steady")
	var c := ClassResource.new(&"combo")
	ok(c.is_pips(), "Combo is shown as pips")
	for i in 7:
		c.gain(1.0)
	eq(c.value, ClassResource.COMBO_MAX, "Combo caps at 5 pips")
	ok(c.is_poised(), "5 pips = Poised")
	eq(c.spend_all(), ClassResource.COMBO_MAX, "a finisher spends every pip")
	eq(c.value, 0.0, "pips are gone after the finisher")
	done()

func test_save_round_trip_every_class() -> void:
	for cls in CLASSES:
		var h := _hero(cls, 12)
		var t := h.skill_tree.tree
		var some := 0
		for n in t.nodes:
			if some >= 6:
				break
			if h.skill_tree.can_rank_up(n.id, 99, 12) == "":
				h.skill_tree.rank_up(n.id, 99, 12)
				some += 1
		if cls == &"knight":
			h.skill_tree.ranks[&"aura_might"] = 2
			h.active_aura = &"aura_might"
		var json := JSON.stringify(h.to_dict())
		var back := HeroData.from_dict(JSON.parse_string(json))
		eq(back.cls.id, cls, "%s class survives a save" % cls)
		eq(back.skill_tree.ranks.size(), h.skill_tree.ranks.size(), "%s skill ranks survive a save" % cls)
		for id in h.skill_tree.ranks:
			eq(back.skill_rank(id), h.skill_rank(id), "%s.%s rank survives" % [cls, id])
		eq(back.active_aura, h.active_aura, "%s active aura survives" % cls)
		near(back.compute_stats().get_stat(&"max_hp"), h.compute_stats().get_stat(&"max_hp"), 0.01, "%s derived HP identical after load" % cls)
	done()

# ------------------------------------------------------------------------------------------------------------ live

func _begin(cls: StringName) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "ts": Engine.time_scale}
	_holder = Node3D.new()
	_holder.name = "SkillTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = _hero(cls, 30)
	_learn_all(Game.hero)
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"start")
	_player.bind(Game.hero)
	Engine.time_scale = 3.0
	await _frames(2)

func _end() -> void:
	Engine.time_scale = float(_saved.get("ts", 1.0))
	for t in TempoParty.actors(_tree()):
		t.free()
	for e in _tree().get_nodes_in_group(&"enemy"):
		e.free()
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

func _dummies() -> Array:
	for e in _tree().get_nodes_in_group(&"enemy"):
		e.free()
	var out := []
	var fwd := _player.forward()
	var side := fwd.cross(Vector3.UP).normalized()
	for off in [Vector3.ZERO, side * 1.3 + fwd * 0.4, -side * 1.3 + fwd * 0.4]:
		var pos: Vector3 = _player.global_position + fwd * 2.3 + off
		var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"hollow_soldier"), 30, [], pos, DataEnemies.DIFFICULTY[1])
		if e:
			e.set_physics_process(false)          # standing targets: no AI, no counter-attacks
			out.append(e)
	return out

func _pool_hp(es: Array) -> float:
	var t := 0.0
	for e in es:
		if is_instance_valid(e):
			t += e.hp if e.alive else 0.0
	return t

## Casts every learned active skill of the class at three standing targets and checks it was paid for and (for
## damaging skills) that it hurt something. A script error inside a skill aborts this test (strict mode).
func _cast_all(cls: StringName) -> void:
	await _begin(cls)
	var t := Game.hero.skill_tree.tree
	var no_damage := [&"buff", &"blink", &"vault", &"veil", &"aura", &"mark"]
	for n in t.nodes:
		if n.get("kind", "skill") != "skill":
			continue
		var sid: StringName = n.get("skill", n.id)
		var s := DB.skill(sid)
		if s == null:
			continue
		_player.cooldowns.clear()
		_player.mana = _player.max_mana()
		_player.hp = _player.max_hp()
		if _player.resource and _player.resource.kind in [&"combo", &"focus", &"valor"]:
			_player.resource.value = _player.resource.max_value
		_player.status.remove(&"stealth")
		var es := _dummies()
		if not es.is_empty():
			var c: Vector3 = es[0].global_position
			_player.aim_override = c
			_player.aim_point = Vector3(c.x, _player.global_position.y, c.z)
		await _frames(2)
		var hp0 := _pool_hp(es)
		var why := _player.skill_block_reason(sid)
		ok(why == "", "%s: %s can be cast with the starting gear (%s)" % [cls, sid, why])
		if why != "":
			continue
		var mana0 := _player.mana
		_player._start_skill(sid)
		if s.is_aura():
			eq(Game.hero.active_aura, sid, "%s: %s switches on" % [cls, sid])
			await _until(func(): return _player.status.has(sid), 2.0)
			ok(_player.status.has(sid), "%s: %s pulses its status onto the Knight" % [cls, sid])
			_player.toggle_aura(sid)
			eq(Game.hero.active_aura, &"", "%s: %s switches off" % [cls, sid])
			continue
		if s.behavior == &"spin":
			for i in 3:                                # the test holds no button: tick the channel directly
				_player.runner.spin_tick(s, _player.skill_params(sid))
				await _frames(3)
			_player._stop_channel()
		else:
			await _until(func(): return _player.action == null, 3.0)
		ok(_player.mana < mana0 + 0.001 or _player.mana_cost(sid) <= 0.0, "%s: %s was paid for" % [cls, sid])
		if not s.behavior in no_damage:
			var hurt := await _until(func(): return _pool_hp(es) < hp0 - 0.01, 4.0)
			if not hurt and s.behavior != &"spin":        # single projectiles can be evaded: one retry
				_player.cooldowns.clear()
				_player.mana = _player.max_mana()
				_player._start_skill(sid)
				hurt = await _until(func(): return _pool_hp(es) < hp0 - 0.01, 4.0)
			ok(hurt, "%s: %s damaged a target in front (%.0f -> %.0f)" % [cls, sid, hp0, _pool_hp(es)])
		ok(is_finite(_player.global_position.length()) and _player.alive, "%s: hero fine after %s" % [cls, sid])
	_end()

## Registered stats plus the generated families (per element, per weapon type, all resistances).
static func _known_stat(st: StringName) -> bool:
	if StatDefs.DEFS.has(st) or st == &"res_all":
		return true
	var s := String(st)
	if s.begins_with("dmg_wt_"):
		return DB.weapon_type(StringName(s.substr(7))) != null
	for prefix in ["res_", "dmg_", "pen_", "added_", "status_"]:
		if s.begins_with(prefix):
			return Elements.KEYS.has(StringName(s.substr(prefix.length())))
	return false

static func _placeholders(t: String) -> Array:
	var out := []
	var re := RegEx.create_from_string("[{]([a-z_0-9]+)[}]")
	for m in re.search_all(t):
		out.append(m.get_string(1))
	return out

func _until(cond: Callable, seconds: float) -> bool:
	var t := 0.0
	while t < seconds:
		if cond.call():
			return true
		await _tree().physics_frame
		t += Engine.time_scale / Engine.physics_ticks_per_second
	return cond.call()

func test_cast_every_knight_skill() -> void:
	await _cast_all(&"knight")
	done()

func test_cast_every_mage_skill() -> void:
	await _cast_all(&"mage")
	done()

func test_cast_every_ranger_skill() -> void:
	await _cast_all(&"ranger")
	done()

func test_cast_every_shadowblade_skill() -> void:
	await _cast_all(&"shadowblade")
	done()
