class_name Spawner
extends Node
## Populates a freshly loaded map from its `enemy_zone` markers (MapBuilder.enemy_zone) and `boss_spawn` markers.
## Pack composition, level (within the map's level range), elite rolls (scaled by difficulty) and the combat director
## are decided here; everything is seeded from the map id + zone name so a map loads the same way every time.

var map: MapRoot
var difficulty := {}
var rng := RandomNumberGenerator.new()
var spawned: Array[Enemy] = []

static func populate(p_map: MapRoot, diff_index: int) -> Spawner:
	var s := Spawner.new()
	s.name = "Spawner"
	s.map = p_map
	s.difficulty = DataEnemies.DIFFICULTY[clampi(diff_index, 0, DataEnemies.DIFFICULTY.size() - 1)]
	p_map.add_child(s)
	var dir := CombatDirector.new()
	dir.name = "CombatDirector"
	dir.configure(s.difficulty)
	p_map.add_child(dir)
	s._spawn_all()
	return s

func _spawn_all() -> void:
	var def := map.def
	if def.is_town:
		return
	for m in map.find_children("EnemyZone_*", "Marker3D", true, false):
		# the boss comes from its boss_spawn marker; "summons" zones are reserved for the boss's adds
		if String(m.name).begins_with("EnemyZone_summons") or (m.get_meta(&"enemies", []) as Array).any(func(id): return DB.enemy(StringName(id)) != null and DB.enemy(StringName(id)).archetype == &"boss"):
			continue
		_spawn_zone(m)
	for b in map.get_tree().get_nodes_in_group(&"boss_spawn") if map.is_inside_tree() else []:
		if not map.is_ancestor_of(b):
			continue
		var bid := StringName(b.get_meta(&"boss", "boss_warden"))
		var flag := StringName(b.get_meta(&"flag", "boss_warden_defeated"))
		if Game.hero and Game.hero.world_flags.get(flag, false):
			continue
		var edef := DB.enemy(bid)
		if edef:
			var e := spawn_enemy(map, edef, def.level_max, [], b.global_position, difficulty)
			e.patrol_radius = 0.0
			e.set_meta(&"boss_flag", flag)
			spawned.append(e)

func _spawn_zone(m: Marker3D) -> void:
	rng.seed = hash(String(map.def.id) + String(m.name))
	var ids: Array = m.get_meta(&"enemies", [])
	var count := int(m.get_meta(&"count", 3))
	var radius := float(m.get_meta(&"radius", 5.0))
	var elite_chance := float(m.get_meta(&"elite_chance", 0.0)) * float(difficulty.get("elite", 1.0))
	var lvl := rng.randi_range(map.def.level_min, map.def.level_max)
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
		var e := spawn_enemy(map, edef, lvl, mods, p, difficulty)
		e.patrol_radius = radius * 0.6
		e.home = m.global_position
		e.zone = m
		e.rotation.y = rng.randf() * TAU
		spawned.append(e)

func _nav_point(p: Vector3) -> Vector3:
	var nm := map.nav_region.get_navigation_map() if map.nav_region else RID()
	if nm.is_valid():
		var q := NavigationServer3D.map_get_closest_point(nm, p)
		if q.is_finite() and q.distance_to(p) < 4.0:
			return q
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

static func spawn_enemy(parent: Node, def: EnemyDef, lvl: int, mods: Array, pos: Vector3, diff: Dictionary) -> Enemy:
	var e := Enemy.new()
	e.setup(def, lvl, mods, diff)
	e.name = "Enemy_%s_%d" % [def.id, parent.get_child_count()]
	parent.add_child(e)
	e.global_position = pos + Vector3.UP * 0.1
	e.home = pos
	return e
