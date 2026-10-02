class_name QuakeTeam
extends RefCounted
## The Quake Team (bh-017): up to three AI allies a single-player hero can call with the `quake team` cheat. This class
## creates them, puts them into the world beside the player whenever a map loads, brings a fallen one back on its feet
## a little later, shares out the gold of the fight, and keeps them level with their leader.
## Multiplayer has no Quake Team (allies there are real players).

const MAX := 3
const RESPAWN_DELAY := 14.0
## Share of a kill's gold each mate earns (it is theirs to spend at the shops).
const GOLD_SHARE := 0.8

static var _connected := false

static func team(hero: HeroData) -> Array:
	return hero.quake_team if hero else []

static func actors(tree: SceneTree = null) -> Array:
	var t := tree if tree else Engine.get_main_loop() as SceneTree
	if t == null:
		return []
	return t.get_nodes_in_group(&"quake_ally").filter(func(n): return is_instance_valid(n) and not n.is_queued_for_deletion())

static func actor_for(mate: QuakeMate) -> QuakeAlly:
	for a in actors():
		if a is QuakeAlly and (a as QuakeAlly).mate == mate:
			return a
	return null

## Call the next mate. Returns {ok, text}.
static func summon(hero: HeroData, player: Node3D) -> Dictionary:
	if hero == null or player == null or not is_instance_valid(player):
		return {"ok": false, "text": "There is no hero to fight beside."}
	if Net.is_active():
		return {"ok": false, "text": "The Quake Team can only be summoned in Single Player."}
	if hero.quake_team.size() >= MAX:
		return {"ok": false, "text": "The Quake Team is full (%d of %d)." % [hero.quake_team.size(), MAX]}
	var taken := hero.quake_team.map(func(m): return (m as QuakeMate).class_id())
	var cls := QuakeMate.pick_class(hero, taken)
	var uid := 1
	for m in hero.quake_team:
		uid = maxi(uid, (m as QuakeMate).uid + 1)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%s/quake/%d" % [hero.hero_name, uid]) ^ Time.get_ticks_usec()
	var mate := QuakeMate.create(hero, uid, cls, rng)
	hero.quake_team.append(mate)
	var a: QuakeAlly = null
	if Game.current_map != null and is_instance_valid(Game.current_map):
		a = spawn_one(Game.current_map, player, hero, mate, hero.quake_team.size() - 1)
	Events.quake_team_changed.emit()
	return {"ok": true, "text": "Quake Team: %s the %s (level %d) joins you - %d of %d." % [mate.display_name(), mate.hero.cls.display_name, mate.level(),
		hero.quake_team.size(), MAX], "mate": mate, "actor": a}

## Put every mate into the world beside `player` (Game.load_map calls this after the player's own Tempos).
static func spawn_for(map: Node3D, player: Node3D, hero: HeroData) -> void:
	if map == null or player == null or hero == null or hero.quake_team.is_empty() or Net.is_active():
		return
	for i in hero.quake_team.size():
		var mate: QuakeMate = hero.quake_team[i]
		if actor_for(mate) != null:
			continue
		mate.sync_with(hero)
		mate.tdata.fallen = false
		spawn_one(map, player, hero, mate, i)

static func spawn_one(map: Node3D, player: Node3D, hero: HeroData, mate: QuakeMate, slot: int) -> QuakeAlly:
	var a := QuakeAlly.new().bind_mate(mate, player, slot)
	map.add_child(a)
	var f: Vector3 = player.global_transform.basis.z.slide(Vector3.UP).normalized()
	if f.length() < 0.1:
		f = Vector3.BACK
	var side := f.cross(Vector3.UP) * (2.4 if slot % 2 == 0 else -2.4)
	var spot := player.global_position - f * (2.6 + 0.8 * float(slot)) + side
	if map.is_inside_tree():
		spot = CombatQuery.reachable_point(map.get_world_3d(), player.global_position, spot, 0.4)
		spot = CombatQuery.ground_at(map.get_world_3d(), spot + Vector3.UP * 1.5)
	a.global_position = spot + Vector3.UP * 0.05
	a.rotation.y = player.rotation.y
	FX.spawn(VFXLib.particles(Color(1.0, 0.85, 0.5, 0.8), 24, 0.8, true, 0.1, 2.0, 180.0, Vector3(0, 1.5, 0), 0.5), spot + Vector3.UP)
	# the Tempo the mate has bound follows the mate
	TempoParty.spawn_for(map, a, mate.hero)
	return a

## A mate went down: it is back on its feet beside the player after a short while.
static func on_ally_fell(a: QuakeAlly) -> void:
	var mate := a.mate
	var tree := a.get_tree()
	if tree == null or mate == null:
		return
	tree.create_timer(RESPAWN_DELAY).timeout.connect(func() -> void:
		var hero := Game.hero
		var player := Game.player as Node3D
		var map := Game.current_map
		if hero == null or not hero.quake_team.has(mate) or player == null or not is_instance_valid(player) or map == null or not is_instance_valid(map):
			return
		if actor_for(mate) != null or Net.is_active():
			return
		mate.tdata.fallen = false
		mate.tdata.hp_frac = 0.6
		mate.tdata.mana_frac = 0.6
		spawn_one(map, player, hero, mate, hero.quake_team.find(mate)))

## The leader gained a level: every mate catches up (and spends the points a level brings).
static func sync_owner(hero: HeroData) -> void:
	for m in hero.quake_team:
		var mate := m as QuakeMate
		var before := mate.level()
		if mate.sync_with(hero) and mate.level() > before:
			Events.notify.emit("%s reaches level %d." % [mate.display_name(), mate.level()], &"info")
		var a := actor_for(mate)
		if a:
			a.mark_stats_dirty()

## bh-030: send a mate home (the `quake quake` cheat, the Debug console): the most recently called one unless `mate`
## is given. Its actor and its Tempo leave the world at once. Returns {ok, text}.
static func dismiss(hero: HeroData, mate: QuakeMate = null) -> Dictionary:
	if hero == null or hero.quake_team.is_empty():
		return {"ok": false, "text": "No Quake Team ally is with you."}
	if mate == null or not hero.quake_team.has(mate):
		mate = hero.quake_team[-1]
	var a := actor_for(mate)
	if a:
		FX.spawn(VFXLib.particles(Color(1.0, 0.85, 0.5, 0.8), 24, 0.8, true, 0.1, 2.0, 180.0, Vector3(0, 1.5, 0), 0.5), a.global_position + Vector3.UP)
		a.queue_free()
	for t in TempoParty.actors():
		if t is Tempo and (t as Tempo).hero == mate.hero:
			t.queue_free()
	hero.quake_team.erase(mate)
	Events.quake_team_changed.emit()
	return {"ok": true, "text": "Quake Team: %s leaves your side (%d of %d remain)." % [mate.display_name(), hero.quake_team.size(), MAX]}

## No Quake Team in a multiplayer session: whoever is standing in the world leaves.
static func dismiss_actors() -> void:
	for a in actors():
		a.queue_free()

# ---- what the team earns --------------------------------------------------------------------------------------------

static func connect_events() -> void:
	if _connected:
		return
	_connected = true
	Events.actor_died.connect(_on_actor_died)
	Events.stage_cleared.connect(_on_stage_cleared)

static func _on_actor_died(actor: Node, _killer: Node) -> void:
	var hero := Game.hero
	if hero == null or hero.quake_team.is_empty() or not (actor is Enemy):
		return
	var e := actor as Enemy
	var player := Game.player as Node3D
	if player == null or not is_instance_valid(player) or e.global_position.distance_to(player.global_position) > 50.0:
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = e.get_instance_id() ^ Time.get_ticks_usec()
	var g := rng.randi_range(e.def.gold.x, e.def.gold.y)
	g = int(round(float(g) * (1.0 + 0.12 * float(e.level - 1)) * (3.0 if e.is_elite else 1.0) * (4.0 if e.is_miniboss() else 1.0) * GOLD_SHARE))
	if e.is_boss:
		g = int(round(float(g) * 3.0))
	if g <= 0:
		return
	for m in hero.quake_team:
		(m as QuakeMate).hero.inventory.gold += g

static func _on_stage_cleared(map_id: StringName) -> void:
	var hero := Game.hero
	var def := DB.map_def(map_id)
	if hero == null or hero.quake_team.is_empty() or def == null:
		return
	var gold := int(round(float(25 + 15 * def.level_max) * GOLD_SHARE))
	for m in hero.quake_team:
		(m as QuakeMate).hero.inventory.gold += gold
