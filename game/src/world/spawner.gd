class_name Spawner
extends Node
## Populates a freshly loaded map from its `enemy_zone` markers (MapBuilder.enemy_zone) and `boss_spawn` markers.
## Pack composition, level (within the map's level range), elite rolls (scaled by difficulty) and the combat director
## are decided here; everything is seeded from the map id + zone name so a map loads the same way every time.

var growth := DungeonGrowth.profile(1)
var dungeon: StringName = &""
var depth := 0
var map: MapRoot
var difficulty := {}
var rng := RandomNumberGenerator.new()
var spawned: Array[Enemy] = []
## Camps (enemy zones) of this visit: zone name -> Array[Enemy]; a camp is cleared when all of its enemies are dead.
## When every camp of a combat map is cleared the stage is cleared (once per visit) — bh-007.
var camps := {}
var cleared_camps := {}
var minibosses: Array[Enemy] = []
var stage_done := false

static func populate(p_map: MapRoot, diff_index: int) -> Spawner:
	var s := Spawner.new()
	s.name = "Spawner"
	s.map = p_map
	var parsed := DataDungeons.parse(p_map.def.id)
	s.dungeon = parsed[0]
	if s.dungeon != &"":
		s.growth = DungeonGrowth.for_hero(Game.hero, s.dungeon)
		s.depth = int(parsed[1]) - DataDungeons.floor_count(s.dungeon)
	s.difficulty = DataEnemies.DIFFICULTY[clampi(diff_index, 0, DataEnemies.DIFFICULTY.size() - 1)]
	if s.dungeon != &"" and DataDungeons.is_special(s.dungeon):
		# bh-028: special dungeons are very strong on every difficulty
		var power: Dictionary = DataDungeons.get_def(s.dungeon).get("power", {})
		s.difficulty = s.difficulty.duplicate()
		s.difficulty["hp"] = float(s.difficulty.get("hp", 1.0)) * float(power.get("hp", 1.0))
		s.difficulty["damage"] = float(s.difficulty.get("damage", 1.0)) * float(power.get("damage", 1.0))
	p_map.add_child(s)
	var dir := CombatDirector.new()
	dir.name = "CombatDirector"
	dir.configure(s.difficulty)
	p_map.add_child(dir)
	s._spawn_all()
	s._warm_summons()
	Events.actor_died.connect(s._on_actor_died)
	return s

## bh-037: monsters that call others into the fight (summons, burrows, eggs, mirror images, rifts, nests, parasites,
## Verdigast's rot buds: Enemy.TraitsX.minion_kinds) spawned a kind the map
## had never shown: its model read from disk and its outfit baked on the blow, 40-60 ms frames mid-fight. While the map
## loads, every kind a monster here can call gets one hidden, idle visual built the way Enemy builds it, kept until the map
## goes, so its model, weapon and baked outfit stay loaded.
func _warm_summons() -> void:
	var present := {}
	for e in spawned:
		if is_instance_valid(e) and not present.has(e.def.id):
			present[e.def.id] = true
			if e.visual:
				e.visual.warm_see_through()       # its corpse will fade (and some kinds go see-through alive)
	var want := {}
	for id in present:
		var d := DB.enemy(id)
		if d == null:
			continue
		for k in Enemy.TraitsX.minion_kinds(d):
			want[k] = true
			var kd := DB.enemy(k)             # a rift's shades, a nest's drones: what a called kind calls in turn
			if kd:
				for k2 in Enemy.TraitsX.minion_kinds(kd):
					want[k2] = true
	var holder := Node3D.new()
	holder.name = "WarmSummons"
	holder.visible = false
	holder.process_mode = Node.PROCESS_MODE_DISABLED
	add_child(holder)
	for id in want:
		var d := DB.enemy(id)
		if d == null or present.has(id):
			continue
		var v := CharacterVisual.new()
		holder.add_child(v)
		var persona := Persona.for_enemy(d)
		if not persona.is_empty():
			v.setup(Persona.MODEL, d.model_scale * float(persona.get("size", 1.0)), d.tint, &"")
			Persona.apply(v, persona)
		else:
			v.setup(CreatureSwaps.model(d.model), d.model_scale, d.tint, &"")
		if d.weapon != "":
			v.attach_weapon(&"main", d.weapon)
		v.warm_see_through()
		if v.tree:
			v.tree.active = false

func _spawn_all() -> void:
	var def := map.def
	# bh-013: a raided dungeon's floors stay empty until it recovers (its champions still come back)
	var dg: StringName = DataDungeons.parse(def.id)[0]
	var quiet := dg != &"" and depth <= 0 and DataDungeons.recovering(Game.hero, dg)
	for m in map.find_children("EnemyZone_*", "Marker3D", true, false):
		if quiet:
			break
		# towns stay safe inside their walls: only "wild" camps out on the roads beyond them spawn (bh-012)
		if def.is_town and not m.get_meta(&"wild", false):
			continue
		# the boss comes from its boss_spawn marker; "summons" zones are reserved for the boss's adds
		if String(m.name).begins_with("EnemyZone_summons") or (m.get_meta(&"enemies", []) as Array).any(func(id): return DB.enemy(StringName(id)) != null and DB.enemy(StringName(id)).archetype == &"boss"):
			continue
		_spawn_zone(m)
	for b in map.get_tree().get_nodes_in_group(&"boss_spawn") if map.is_inside_tree() else []:
		if not map.is_ancestor_of(b):
			continue
		var bid := StringName(b.get_meta(&"boss", "boss_warden"))
		var flag := StringName(b.get_meta(&"flag", "boss_warden_defeated"))
		var bdg := StringName(b.get_meta(&"dungeon", ""))
		if bdg != &"":
			# a dungeon boss never returns once raided (bh-013); DungeonRuntime records the raid, its Usurper holds the sanctum
			if DataDungeons.boss_gone(Game.hero, bdg):
				continue
		elif Game.hero and Game.hero.world_flags.get(flag, false):
			continue
		var edef := DB.enemy(bid)
		if edef:
			var e := spawn_enemy(map, edef, def.level_max, [], b.global_position, difficulty)
			e.set_meta(&"dungeon_reward_bonus", float(growth.reward_bonus))
			e.patrol_radius = 0.0
			if bdg == &"":
				e.set_meta(&"boss_flag", flag)
			spawned.append(e)
	_spawn_minibosses()

## Named champions of this map (DataMinibosses) that are not resting after a recent defeat.
func _spawn_minibosses() -> void:
	for md in DataMinibosses.on_map(map.def.id):
		if DataMinibosses.resting(Game.hero, md.id):
			continue
		# a dungeon's Usurper (bh-013) only takes the sanctum once the boss is gone
		if md.has("raid_only") and not DataDungeons.boss_gone(Game.hero, StringName(md.raid_only)):
			continue
		var edef := DB.enemy(md.enemy)
		if edef == null:
			push_warning("Unknown miniboss enemy %s" % md.enemy)
			continue
		var p: Vector2 = md.pos
		var ground := Vector3(p.x, 0.0, p.y)
		if map.is_inside_tree():
			ground = map.to_global(ground)
			ground.y = map.global_position.y + NpcDirectory.ground_height(map, Vector3(p.x, float(md.get("y", 0.0)), p.y))
		var e := Enemy.new()
		e.setup(edef, CombatGrowth.encounter_level(map.def.level_max + int(md.get("level_bonus", 0)), int(growth.level) if dungeon != &"" else (Game.hero.progress.level if Game.hero != null else 1)), md.get("mods", []), difficulty)
		e.set_meta(&"dungeon_reward_bonus", float(growth.reward_bonus))
		e.make_miniboss(md)
		e.name = "Miniboss_%s" % md.id
		map.add_child(e)
		e.global_position = _nav_point(ground) + Vector3.UP * 0.1
		e.home = e.global_position
		e.patrol_radius = 2.0
		e.rotation.y = rng.randf() * TAU
		minibosses.append(e)
		spawned.append(e)

func _spawn_zone(m: Marker3D) -> void:
	rng.seed = hash(String(map.def.id) + String(m.name))
	var ids: Array = m.get_meta(&"enemies", [])
	if dungeon != &"":
		ids = DungeonGrowth.pool(dungeon, ids, growth, hash(String(m.name)))
	var count := int(m.get_meta(&"count", 3)) + int(growth.pack_bonus)
	var radius := float(m.get_meta(&"radius", 5.0))
	var elite_chance := float(m.get_meta(&"elite_chance", 0.0)) * float(difficulty.get("elite", 1.0))
	var lvl := rng.randi_range(map.def.level_min, map.def.level_max)
	if m.has_meta(&"levels"):
		# a camp with its own level range (bh-012: wild camps outside the town walls)
		var lv: Vector2i = m.get_meta(&"levels")
		lvl = rng.randi_range(lv.x, lv.y)
	elite_chance = clampf(elite_chance + float(growth.elite_bonus), 0.0, 0.9) if elite_chance < 1.0 else 1.0
	var pack_elite := rng.randf() < elite_chance
	var elite_idx := rng.randi_range(0, maxi(0, count - 1)) if pack_elite else -1
	for i in count:
		var eid := StringName(ids[i % ids.size()]) if not ids.is_empty() else &"hollow_soldier"
		var edef := DB.enemy(eid)
		if edef == null:
			push_warning("Unknown enemy %s in zone %s" % [eid, m.name])
			continue
		var ang := TAU * float(i) / float(count) + rng.randf_range(-0.4, 0.4)
		var p := m.global_position + Vector3(cos(ang), 0, sin(ang)) * rng.randf_range(0.6, radius * 0.7)
		p = _nav_point(p)
		var mods: Array = []
		if i == elite_idx and edef.can_be_elite:
			mods = roll_elite_mods(rng, lvl)
			if int(growth.stage) == 2:
				for extra in [&"shielded", &"swift"]:
					if not mods.has(extra) and mods.size() < 3:
						mods.append(extra)
		var guardian := {}
		if depth > 0 and i == elite_idx and String(m.name) == "EnemyZone_" + DataDungeons.SEAL_ZONE:
			guardian = {"id": StringName("depth_%s_%d" % [dungeon, depth]), "name": "Guardian of %s" % DungeonGrowth.NAMES[depth - 1],
				"title": "Greater Depth Guardian" if int(growth.stage) == 2 else "Depth Guardian", "hp": 1.35, "damage": 1.08, "scale": 1.15}
		var e := spawn_enemy(map, edef, lvl, mods, p, difficulty, guardian)
		if dungeon != &"":
			e.set_meta(&"dungeon_reward_bonus", float(growth.reward_bonus))
			if not guardian.is_empty():
				e.set_meta(&"depth_guardian", true)
				minibosses.append(e)
		e.patrol_radius = radius * 0.6
		e.home = m.global_position
		e.zone = m
		e.rotation.y = rng.randf() * TAU
		spawned.append(e)
		camps.get_or_add(String(m.name).trim_prefix("EnemyZone_"), []).append(e)
	_pair_twins(String(m.name).trim_prefix("EnemyZone_"), lvl)

## bh-013: Soulbound Twins always come in pairs: the twins of a camp are paired up, an odd one gets a partner.
func _pair_twins(zone: String, lvl: int) -> void:
	var twins: Array = (camps.get(zone, []) as Array).filter(func(x): return x is Enemy and (x as Enemy).has_trait(&"twin"))
	if twins.size() % 2 == 1:
		var last: Enemy = twins[twins.size() - 1]
		var p := _nav_point(last.global_position + Vector3(1.6, 0, 0.8))
		var mate := spawn_enemy(map, last.def, lvl, [], p, difficulty)
		mate.patrol_radius = last.patrol_radius
		mate.home = last.home
		mate.zone = last.zone
		spawned.append(mate)
		camps[zone].append(mate)
		twins.append(mate)
	for i in range(0, twins.size() - 1, 2):
		twins[i + 1].set_meta(&"twin_warm", true)
		Enemy.TraitsX.pair(twins[i], twins[i + 1])

## Where a monster may stand near `p`: the closest navmesh point (a camp marker's height is only a hint — the ground
## rises and falls across a camp, and a bridge camp's marker sits in the ravine below the deck). Without a usable
## navmesh answer, the ground under `p` found by a ray from above: never the raw marker height, which buried monsters
## in hillsides (they fell out of the world and paid the hero experience) or left them under bridges (bh-011).
func _nav_point(p: Vector3) -> Vector3:
	var nm := map.nav_region.get_navigation_map() if map.nav_region else RID()
	if nm.is_valid() and NavigationServer3D.map_get_iteration_id(nm) > 0:
		var q := NavigationServer3D.map_get_closest_point(nm, p)
		if q.is_finite() and q != Vector3.ZERO and Vector2(q.x - p.x, q.z - p.z).length() < 4.0 and absf(q.y - p.y) < 9.0:
			return q
	if map.is_inside_tree():
		var local := map.to_local(p)
		return map.to_global(Vector3(local.x, NpcDirectory.ground_height(map, local), local.z))
	return p

## One or two elite modifiers (two from level 6).
static func roll_elite_mods(r: RandomNumberGenerator, lvl: int) -> Array:
	var keys := DB.elite_mods.keys()
	keys.sort()
	var n := 2 if lvl >= 6 and r.randf() < 0.45 else 1
	var out := []
	while out.size() < n:
		var k: StringName = keys[r.randi_range(0, keys.size() - 1)]
		if not out.has(k):
			out.append(k)
	return out

static func spawn_enemy(parent: Node, def: EnemyDef, lvl: int, mods: Array, pos: Vector3, diff: Dictionary, guardian: Dictionary = {}) -> Enemy:
	var e := Enemy.new()
	var visit_level := Game.hero.progress.level if Game.hero != null else 1
	var spawner := parent.get_node_or_null("Spawner") as Spawner
	if spawner != null and spawner.dungeon != &"":
		visit_level = int(spawner.growth.level)
	lvl = CombatGrowth.encounter_level(lvl, visit_level, def.archetype == &"boss")
	e.setup(def, lvl, mods, diff)
	if e.is_boss and Game.hero != null:
		var baseline := EnemyStats.build(def, lvl, diff, [], false, true)
		e.encounter_hp_mult = EnemyStats.boss_health(Game.hero, baseline) / baseline.get_stat(&"max_hp")
	if not guardian.is_empty():
		e.make_miniboss(guardian)
	e.name = "Enemy_%s_%d" % [def.id, parent.get_child_count()]
	parent.add_child(e)
	e.global_position = pos + Vector3.UP * 0.1
	e.home = pos
	return e

# ---- Camps and stage clears (bh-007) ----------------------------------------------------------------------------

func camp_total() -> int:
	return camps.size()

func camps_cleared() -> int:
	return cleared_camps.size()

func _camp_alive(list: Array) -> bool:
	for e in list:
		if is_instance_valid(e) and (e as Enemy).alive:
			return true
	return false

func _on_actor_died(actor: Node, _killer: Node) -> void:
	if not (actor is Enemy) or not is_instance_valid(map) or not map.is_inside_tree():
		return
	for zone in camps:
		if cleared_camps.has(zone) or not (camps[zone] as Array).has(actor):
			continue
		if not _camp_alive(camps[zone]):
			cleared_camps[zone] = true
			Events.camp_cleared.emit(map.def.id, zone, camps.size() - cleared_camps.size(), camps.size())
	if not stage_done and not camps.is_empty() and cleared_camps.size() >= camps.size():
		stage_done = true
		if Game.hero:
			Game.hero.stages_cleared[map.def.id] = int(Game.hero.stages_cleared.get(map.def.id, 0)) + 1
			Game.hero.add_clear()
		Events.stage_cleared.emit(map.def.id)

## The current map's spawner (for the HUD's stage tracker), or null.
static func current() -> Spawner:
	if Game.current_map == null or not is_instance_valid(Game.current_map):
		return null
	return Game.current_map.get_node_or_null(^"Spawner") as Spawner
