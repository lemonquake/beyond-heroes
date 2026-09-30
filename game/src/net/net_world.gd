class_name NetWorld
## A map's combat state can pass to a remaining party member without respawning cleared camps.

static func capture(enemies: Dictionary) -> Dictionary:
	var live := []
	for e: Enemy in enemies.values():
		if is_instance_valid(e) and e.alive and not e.net_replica:
			var info := Net.enemy_info(e)
			info.merge({"home": e.home, "patrol": e.patrol_radius, "shield": e.shield_hp,
				"phase": e.phase, "enraged": e.enraged, "risen": e.risen,
				"zone": String(e.zone.name).trim_prefix("EnemyZone_") if is_instance_valid(e.zone) else ""})
			live.append(info)
	var sp := Spawner.current()
	return {"difficulty": maxi(0, DataEnemies.DIFFICULTY.find(sp.difficulty)) if sp else Game.difficulty, "enemies": live, "camps": sp.camps.keys() if sp else [],
		"cleared": sp.cleared_camps.duplicate() if sp else {}, "done": sp.stage_done if sp else false}

static func make_enemy(info: Dictionary, replica: bool) -> Enemy:
	var def := DB.enemy(StringName(info.get("def", "")))
	if def == null:
		return null
	var e := Enemy.new()
	e.net_replica = replica
	e.encounter_hp_mult = maxf(0.00000001, float(info.get("encounter_hp_mult", 1.0)))
	e.setup(def, int(info.lvl), (info.mods as Array).map(func(m): return StringName(m)),
		DataEnemies.DIFFICULTY[clampi(int(info.diff), 0, DataEnemies.DIFFICULTY.size() - 1)])
	var md := DataMinibosses.find(StringName(info.get("mb", "")))
	if md.is_empty() and not (info.get("depth_guardian", {}) as Dictionary).is_empty():
		md = info.depth_guardian
		e.set_meta(&"depth_guardian", true)
	e.set_meta(&"dungeon_reward_bonus", float(info.get("dungeon_reward", 0.0)))
	if not md.is_empty():
		e.make_miniboss(md)
	if String(info.get("flag", "")) != "":
		e.set_meta(&"boss_flag", StringName(info.flag))
	e.risen = bool(info.get("risen", false))
	e.set_meta(&"net_id", int(info.id))
	e.name = "NetworkEnemy_%d" % int(info.id)
	Game.current_map.add_child(e)
	e.global_position = info.pos
	e.rotation.y = float(info.yaw)
	e.net_snap(info.pos, float(info.yaw))
	e.hp = float(info.hp)
	e.home = info.get("home", info.pos)
	e.patrol_radius = float(info.get("patrol", 5.0))
	e.shield_hp = float(info.get("shield", 0.0))
	e.phase = int(info.get("phase", 1))
	e.enraged = bool(info.get("enraged", false))
	return e

static func restore(state: Dictionary) -> void:
	var map := Game.current_map
	var sp := Spawner.new()
	sp.name = "Spawner"
	sp.map = map
	sp.difficulty = DataEnemies.DIFFICULTY[clampi(int(state.get("difficulty", Game.difficulty)), 0, DataEnemies.DIFFICULTY.size() - 1)]
	map.add_child(sp)
	var director := CombatDirector.new()
	director.name = "CombatDirector"
	director.configure(sp.difficulty)
	map.add_child(director)
	for camp in state.get("camps", []):
		sp.camps[camp] = []
	sp.cleared_camps = state.get("cleared", {}).duplicate()
	sp.stage_done = bool(state.get("done", false))
	for info in state.get("enemies", []):
		var e := make_enemy(info, false)
		if e == null:
			continue
		sp.spawned.append(e)
		if e.is_miniboss():
			sp.minibosses.append(e)
		var zone := String(info.get("zone", ""))
		if zone != "":
			sp.camps.get_or_add(zone, []).append(e)
			for marker in map.find_children("EnemyZone_*", "Marker3D", true, false):
				if String(marker.name) == "EnemyZone_" + zone:
					e.zone = marker
	for zone in sp.camps:
		var twins: Array = sp.camps[zone].filter(func(e): return e.has_trait(&"twin"))
		for i in range(0, twins.size() - 1, 2):
			Enemy.TraitsX.pair(twins[i], twins[i + 1])
	Events.actor_died.connect(sp._on_actor_died)
