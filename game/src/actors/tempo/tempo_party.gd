class_name TempoParty
## Puts the hero's standing Tempos into the world beside the player whenever a map loads, keeps their persistent HP /
## mana in step with the TempoData before a map unloads or the game saves, and adds or removes spirits when the
## Tempo-Caller binds, calls back or releases one.

static func actors(tree: SceneTree = null) -> Array:
	var t := tree if tree else Engine.get_main_loop() as SceneTree
	if t == null:
		return []
	return t.get_nodes_in_group(&"tempo").filter(func(n): return is_instance_valid(n) and not n.is_queued_for_deletion())

static func actor_for(uid: int) -> Tempo:
	for a in actors():
		if a is Tempo and a.data and a.data.uid == uid:
			return a
	return null

## Spawn every standing Tempo next to `player` on `map` (called by Game.load_map after the player is placed).
static func spawn_for(map: Node3D, player: Node3D, hero: HeroData) -> Array:
	var out := []
	if map == null or player == null or hero == null:
		return out
	var i := 0
	for t in TempoRules.active(hero):
		if actor_for(t.uid) != null:
			i += 1
			continue
		out.append(spawn_one(map, player, hero, t, i))
		i += 1
	return out

static func spawn_one(map: Node3D, player: Node3D, hero: HeroData, t: TempoData, slot: int) -> Tempo:
	var a := Tempo.new().setup(t, hero, player, slot)
	map.add_child(a)
	var f: Vector3 = player.global_transform.basis.z.slide(Vector3.UP).normalized()
	if f.length() < 0.1:
		f = Vector3.BACK
	var side := f.cross(Vector3.UP) * (1.6 if slot % 2 == 0 else -1.6)
	var spot := player.global_position - f * 1.8 + side
	if map.is_inside_tree():
		spot = CombatQuery.reachable_point(map.get_world_3d(), player.global_position, spot, 0.4)
		spot = CombatQuery.ground_at(map.get_world_3d(), spot + Vector3.UP * 1.5)
	a.global_position = spot + Vector3.UP * 0.05
	a.rotation.y = player.rotation.y
	FX.spawn(VFXLib.particles(Color(0.6, 0.95, 1.0, 0.8), 24, 0.8, true, 0.1, 2.0, 180.0, Vector3(0, 1.5, 0), 0.5), spot + Vector3.UP)
	return a

## Write every live Tempo's HP / mana back into its TempoData.
static func sync_all() -> void:
	for a in actors():
		if a is Tempo:
			a.sync_data()

## Bring the world in line with the hero's roster (after binding, calling back or releasing a spirit).
static func refresh(hero: HeroData) -> void:
	var map := Game.current_map
	var player := Game.player
	if hero == null or map == null or player == null or not is_instance_valid(player):
		return
	var keep := {}
	for t in TempoRules.active(hero):
		keep[t.uid] = true
	for a in actors():
		if a is Tempo and (not keep.has(a.data.uid) or not hero.tempos.has(a.data)) and a.alive:
			a.queue_free()
	spawn_for(map, player, hero)

## Same-map relocation (waypoint to itself, falling out of the world): spirits follow the hero at once.
static func regroup(player: Node3D) -> void:
	for a in actors():
		if a is Tempo and a.alive:
			a._rejoin_hero()
