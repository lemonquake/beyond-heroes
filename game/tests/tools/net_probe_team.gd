extends Node
## Three-process ENet regression. All characters use scratch saves (90-92).
## Start host, scout, ally with --role=<role> --class=knight --name=<role> --map=sanctuary --slot=<scratch>.

var role := "host"
var replies := {}
var failures: Array = []
var steps := 0

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--role="):
			role = arg.substr(7)
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout

func check(label: String, value: bool) -> void:
	print("TEAM[%s] %s %s" % [role, "PASS" if value else "FAIL", label])
	if not value:
		failures.append(label)

func _run() -> void:
	for i in 600:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await wait(0.1)
	Game.god_mode = true
	Settings.auto_loot_enabled = false
	if role != "host":
		await wait(2.0)
		check("join requested", Net.join_game("127.0.0.1", 24685) == "")
		await wait(240.0)
		check("probe finished before watchdog", false)
		get_tree().quit(1)
		return
	check("host opened", Net.host_game(24685) == "")
	for i in 600:
		if Net.player_count() == 3 and Net.avatars().size() >= 2:
			break
		await wait(0.1)
	check("three players connected", Net.player_count() == 3)
	var scout := 0
	var ally := 0
	for id in Net.peers:
		if Net.peers[id].get("name", "") == "scout":
			scout = int(id)
		elif Net.peers[id].get("name", "") == "ally":
			ally = int(id)
	if DisplayServer.get_name() != "headless":
		Game.ui_root.open(&"multiplayer")
		await wait(1.0)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://../output/team-multiplayer.png")
		Game.ui_root.close_all()
	if scout == 0 or ally == 0:
		get_tree().quit(1)
		return
	await step(scout, "travel", {"map": "westreach"})
	await step(ally, "travel", {"map": "westreach"})
	check("leader remained in town", Game.current_map_id == &"sanctuary")
	check("first explorer owns remote map", Net.world_owner(&"westreach") == scout)
	await step(scout, "authority", {"value": true})
	await step(ally, "authority", {"value": false})
	await step(ally, "replicas", {})
	await step(scout, "prepare_kill", {})
	await step(ally, "kill", {})
	await step(scout, "dead", {})
	await step(ally, "kill_reward", {})
	# The leader's portal goes to a chosen member's current map without moving the other member.
	check("leader portal begins", Net.team_portal(scout))
	await wait(5.0)
	await wait(2.0)
	check("leader portal changes map", Game.current_map_id == &"westreach" and not Game.travelling)
	check("leader arrival preserves explorer authority", Net.world_owner(&"westreach") == scout and Net._host_shared)
	var av := Net.avatar(scout)
	check("selected member is visible after map transition", av != null)
	var target_pos: Vector3 = Net.status.get(scout, {}).get("pos", Vector3.INF)
	print("TEAM landing player=%s ally=%s avatar=%s" % [Game.player.global_position, target_pos, av != null])
	check("leader lands beside selected member", target_pos.is_finite() and target_pos.distance_to(Game.player.global_position) < 5.0)
	check("portal cooldown blocks repeat", not Net.team_portal(scout))
	await step(scout, "checkpoint", {})
	# Owner leaves; nobody follows and dead monsters remain dead after transfer.
	await step(scout, "travel", {"map": "sanctuary"})
	await wait(2.0)
	check("leader takes over remaining map", Net.is_world_authority() and Game.current_map_id == &"westreach")
	check("handoff keeps killed enemy dead", not Net._host_enemies.has(900001))
	await step(ally, "replicas", {})
	await step(scout, "portal_interrupted", {})
	await step(scout, "portal", {})
	check("member portal reaches leader", Net._peer_map(scout) == "westreach")
	await step(ally, "stale_packet", {})
	await step(ally, "portal_guards", {})
	await step(ally, "remember_stage", {})
	var sp := Spawner.current()
	sp.stage_done = true
	Events.stage_cleared.emit(Game.current_map_id)
	await wait(1.0)
	await step(ally, "stage_award", {})
	# Refusing a summons never moves the player.
	await step(ally, "travel", {"map": "sanctuary"})
	await step(ally, "bad_revive", {})
	check("optional summon sent", Net.summon_party() >= 1)
	await step(ally, "stay", {})
	await step(ally, "travel", {"map": "westreach"})
	# Rejoin gets a new peer id and clean map ownership, without replaying the old portal.
	await step(scout, "rejoin", {})
	for id in Net.peers:
		if Net.peers[id].get("name", "") == "scout":
			scout = int(id)
	await step(scout, "travel", {"map": "westreach"})
	# Leader explores elsewhere, then the new map owner disconnects.
	await Game.travel(&"sanctuary", &"start")
	await wait(2.0)
	var owner := Net.world_owner(&"westreach")
	var remaining := ally if owner == scout else scout
	await step(owner, "leave", {})
	await wait(2.0)
	check("client disconnect leaves other players connected", Net.player_count() == 2)
	check("remote map gets a remaining owner", Net.world_owner(&"westreach") == remaining)
	await step(remaining, "authority", {"value": true})
	await step(remaining, "handoff_state", {})
	ally = remaining
	# Host shutdown leaves the other client playing locally at its current position/map.
	await step(ally, "expect_shutdown", {})
	Net.leave()
	await wait(4.0)
	print("TEAM[host] SUMMARY %d steps, %d failures" % [steps, failures.size()])
	get_tree().quit(0 if failures.is_empty() else 1)

func step(peer: int, action: String, args: Dictionary) -> void:
	steps += 1
	replies.erase(steps)
	_command.rpc_id(peer, steps, action, args)
	for i in 500:
		if replies.has(steps):
			break
		await wait(0.1)
	check("%s on %s" % [action, Net.peers.get(peer, {}).get("name", str(peer))], replies.get(steps, false))

var _reward_before := 0
var _stage_before := 0

@rpc("authority", "reliable")
func _command(serial: int, action: String, args: Dictionary) -> void:
	var result := false
	match action:
		"travel":
			await Game.travel(StringName(args.map), &"start")
			await wait(2.0)
			result = Game.current_map_id == StringName(args.map) and not Game.travelling
		"authority":
			result = Net.is_world_authority() == bool(args.value)
		"replicas":
			await wait(2.0)
			var local := 0
			for e in get_tree().get_nodes_in_group(&"enemy"):
				if e is Enemy and e.alive and not e.net_replica:
					local += 1
			result = Net._host_shared and local == 0 and Net._replicas.size() > 0
		"prepare_kill":
			var e := Enemy.new().setup(DB.enemy(&"hollow_soldier"), 1)
			e.set_meta(&"net_id", 900001)
			Game.current_map.add_child(e)
			e.global_position = Game.player.global_position + Vector3(2, 0, 2)
			e.home = e.global_position
			e.hp = 1.0
			await wait(2.0)
			result = Net._host_enemies.has(900001)
		"kill":
			_reward_before = Game.hero.progress.xp
			var e: Enemy = Net._replicas.get(900001)
			if e:
				var hit := DamageResult.new()
				hit.total = 100.0
				Net.replica_hit(e, hit, DamageRequest.new(), Game.player, e.global_position)
				await wait(1.0)
				result = not Net._replicas.has(900001)
		"dead":
			var e: Enemy = Net._host_enemies.get(900001)
			result = e == null or not e.alive
		"kill_reward":
			result = Game.hero.progress.xp > _reward_before
		"checkpoint":
			Net._send_checkpoint()
			result = true
		"portal_interrupted":
			var before := Game.current_map_id
			var started := Net.team_portal()
			Game.player.teleport_to(Game.player.global_position + Vector3(3, 0, 0))
			await wait(2.0)
			result = started and Net._portal_pending.is_empty() and Game.current_map_id == before
		"portal":
			var started := Net.team_portal()
			await wait(5.0)
			result = started and Game.current_map_id == StringName(Net._peer_map(1)) and not Game.travelling
		"portal_guards":
			Game.player.alive = false
			var dead_blocked := not Net.team_portal()
			Game.player.respawn()
			Net.trade = {"phase": "asking", "peer": 1}
			var trade_blocked := not Net.team_portal()
			Net.trade = {}
			result = dead_blocked and trade_blocked and not Net.team_portal(Net.my_id()) and not Net.team_portal(-42)
		"remember_stage":
			_stage_before = int(Game.hero.stages_cleared.get(Game.current_map_id, 0))
			result = true
		"stage_award":
			result = int(Game.hero.stages_cleared.get(Game.current_map_id, 0)) == _stage_before + 1 and Spawner.current().stage_done
		"handoff_state":
			result = not Net._host_enemies.has(900001) and Spawner.current() != null and Spawner.current().stage_done
		"rejoin":
			Net.leave()
			await wait(1.0)
			var error := Net.join_game("127.0.0.1", 24685)
			await wait(6.0)
			result = error == "" and Net.is_client() and Net._arrived and Net._portal_pending.is_empty()
		"stale_packet":
			var count := Net._replicas.size()
			Net._enemy_spawn("sanctuary", -5, [{"id": 42}])
			Net._enemy_died("sanctuary", -5, 900001, 1, "death")
			result = count == Net._replicas.size()
		"bad_revive":
			Game.player.alive = false
			Net._revived("forged sender")
			result = not Game.player.alive
			Game.player.respawn()
		"stay":
			await wait(1.0)
			Net.answer_summon(false)
			await wait(1.0)
			result = Game.current_map_id == &"sanctuary"
		"leave":
			_result.rpc_id(1, serial, true)
			await wait(0.5)
			Net.leave()
			await wait(2.0)
			check("leaving preserves current map", Game.current_map_id == &"westreach")
			get_tree().quit(0 if failures.is_empty() else 1)
			return
		"expect_shutdown":
			_result.rpc_id(1, serial, true)
			await wait(3.0)
			check("host closed: playable local world", not Net.is_active() and Game.current_map_id == &"westreach" and Spawner.current() != null)
			get_tree().quit(0 if failures.is_empty() else 1)
			return
	check(action, result)
	_result.rpc_id(1, serial, result)

@rpc("any_peer", "reliable")
func _result(serial: int, result: bool) -> void:
	replies[serial] = result
