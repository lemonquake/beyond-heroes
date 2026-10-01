extends Node
## Two-machine probe for bh-028's Sand Arena over the network. Run two copies on one PC (hidden save slots only):
##   godot --headless --path game res://tests/tools/net_probe_arena.tscn -- --role=host --class=knight --slot=94 --map=wyman_outpost
##   godot --headless --path game res://tests/tools/net_probe_arena.tscn -- --role=join --class=mage --slot=93 --map=wyman_outpost
## Checks (ARENA[role] ok/FAIL lines): only the host runs the adventurers and the client sees them; they are of the
## party's highest level (the client's 40, not the host's 20); a client's blow on an adventurer lands on the host's real
## one and the number comes back; the host's blow on the client's hero lands on the client, scaled and capped; each
## sees the other's hero as a rival only while both stand on the sand.

var args := {}
var role := "host"
var fails: Array = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("ARENA[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

func _wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout

func _until(cond: Callable, limit := 30.0) -> bool:
	var t := 0.0
	while t < limit:
		if cond.call():
			return true
		await _wait(0.1)
		t += 0.1
	return false

func _run() -> void:
	for i in 400:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await _wait(0.1)
	await _wait(1.0)
	var h := Game.hero
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(20 if role == "host" else 40) - h.progress.total_xp))
	h.stats_dirty.emit()
	Net.update_profile()
	if role == "host":
		await _host()
	else:
		await _client()
	print("ARENA[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

func _client_id() -> int:
	for id in Net.peers:
		if int(id) != 1:
			return int(id)
	return 0

func _into_arena(off := Vector3.ZERO) -> void:
	var a := ArenaGrounds.active()
	var p := Game.player as Player
	p.global_position = CombatQuery.ground_at(p.get_world_3d(), a.gate + (a.center - a.gate).normalized() * 4.0 + off + Vector3.UP * 2.0) + Vector3.UP * 0.05
	p.velocity = Vector3.ZERO

func _blow(attacker: Player) -> DamageRequest:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = attacker.stats
	req.use_weapon = true
	req.weapon_mult = 3.0
	req.evadable = false
	req.blockable = false
	req.label = "probe blow"
	return req

func _host() -> void:
	var arena := ArenaGrounds.active()
	var from_client := [0]
	Events.damage_dealt.connect(func(victim: Node, r: DamageResult, _pos: Vector3, attacker: Node) -> void:
		if victim is ArenaFighter and attacker is NetAvatar and r != null and r.total > 0:
			from_client[0] += 1)
	_check("the outpost has the arena", arena != null)
	_check("hosted (%s)" % Net.host_game(), Net.is_host())
	await _until(func() -> bool: return Net.player_count() >= 2, 40.0)
	var cid := _client_id()
	_check("the client joined", cid != 0)
	await _until(func() -> bool: return int(Net.peers.get(cid, {}).get("level", 0)) == 40, 20.0)
	_check("the client's level arrived (%d)" % int(Net.peers.get(cid, {}).get("level", 0)), int(Net.peers.get(cid, {}).get("level", 0)) == 40)
	await _until(func() -> bool: return Net.is_world_authority(), 20.0)
	_check("the host runs the outpost", Net.is_world_authority())
	# fresh adventurers, now that the party is complete: two of them, and keep them out of the way
	for f in arena.fighters():
		f.free()
	arena.max_fighters = 2
	arena._refill_t = 0.0
	await _until(func() -> bool: return arena.fighters().size() >= 2, 20.0)
	_check("two adventurers walked in", arena.fighters().size() >= 2)
	for f in arena.fighters():
		_check("%s is level %d (the party's highest, 40)" % [f.display_name, f.level], f.level == 40)
	_into_arena(Vector3(3, 0, 0))
	# the client comes onto the sand: its hero becomes a rival here
	await _until(func() -> bool:
		var a := Net.avatar(cid)
		return a != null and arena.contains(a.global_position), 40.0)
	var av := Net.avatar(cid)
	_check("the client's hero stands on the sand", av != null and arena.contains(av.global_position))
	if av == null:
		Net.leave()
		return
	await _until(func() -> bool: return av.arena_hostile(), 5.0)
	_check("and is a rival here (layer and target group)", av.arena_hostile() and av.collision_layer == BH.LAYER_ENEMY and av.is_in_group(&"arena_target"))
	await _wait(1.0)
	# strike the client's hero three times
	for i in 3:
		av.receive_hit(_blow(Game.player as Player), Game.player)
		await _wait(0.6)
	var hit := await _until(func() -> bool: return from_client[0] > 0, 25.0)
	_check("the client's blows landed on the real adventurers here (%d)" % from_client[0], hit)
	await _wait(10.0)
	Net.leave()

func _client() -> void:
	await _wait(3.0)
	Net.join_game(NetCodec.room_code("127.0.0.1", Net.PORT, Net.PORT))
	await _until(func() -> bool: return Net.is_client() and not Net.connecting and not Net.following and not Game.travelling, 40.0)
	await _wait(2.0)
	_check("joined the host at the outpost", Net.is_client() and Game.current_map_id == &"wyman_outpost")
	var arena := ArenaGrounds.active()
	await _wait(3.0)
	_check("no adventurers of our own (the host runs them)", arena.fighters().is_empty())
	_into_arena()
	var seen := func() -> Array:
		return Net.avatars().filter(func(a): return (a as NetAvatar).arena_fighter and a.alive)
	await _until(func() -> bool: return (seen.call() as Array).size() >= 2 and (seen.call()[0] as NetAvatar).level == 40, 40.0)
	var fav: Array = seen.call()
	_check("the host's adventurers are here (%d)" % fav.size(), fav.size() >= 2)
	if fav.is_empty():
		Net.leave()
		return
	var target: NetAvatar = fav[0]
	_check("at level 40", target.level == 40)
	_check("as rivals (enemy layer, targetable)", target.collision_layer == BH.LAYER_ENEMY and target.is_in_group(&"arena_target"))
	# watch our own health and the numbers that come back
	var p := Game.player as Player
	var landed := [0]
	Events.damage_dealt.connect(func(victim: Node, r: DamageResult, _pos: Vector3, attacker: Node) -> void:
		if victim == target and attacker == Game.player and r.total > 0:
			landed[0] += 1)
	var worst := [0.0]
	var mhp := p.max_hp()
	p.hit_taken.connect(func(r: DamageResult) -> void:
		worst[0] = maxf(worst[0], float(r.total)))
	var before := p.hp
	for i in 4:
		target.receive_hit(_blow(p), p)
		await _wait(0.4)
	var back := await _until(func() -> bool: return landed[0] > 0, 15.0)
	_check("our blows on the host's adventurer came back as numbers (%d)" % landed[0], back)
	await _until(func() -> bool: return Net.avatar(1) != null and Net.avatar(1).arena_hostile(), 15.0)
	var host_av := Net.avatar(1)
	_check("the host's hero is a rival while we both stand on the sand", host_av != null and host_av.arena_hostile())
	var hurt := await _until(func() -> bool: return worst[0] > 0.0, 20.0)
	_check("the host's blows (or an adventurer's) reached us (worst %d of %d max HP)" % [worst[0], mhp], hurt)
	_check("no single blow took more than 20%", worst[0] <= mhp * CombatBudget.PVP_BLOW_CAP + 1.0)
	# off the sand: not a rival any more
	var a := ArenaGrounds.active()
	p.global_position = CombatQuery.ground_at(p.get_world_3d(), a.gate + a.gate_out * 9.0 + Vector3.UP * 2.0) + Vector3.UP * 0.05
	await _wait(1.0)
	_check("outside, the host's hero is a friend again", host_av == null or not host_av.arena_hostile())
	print("ARENA[join] hp before %d after %d" % [before, p.hp])
	await _wait(3.0)
	Net.leave()
