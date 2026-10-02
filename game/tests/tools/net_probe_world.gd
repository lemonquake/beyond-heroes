extends Node
## Real HTTPS + ENet client that loads a real map and exercises who runs a map's combat (bh-032). Test accounts only.
##   --scenario=handoff   two clients share a map; whoever owns it leaves; the other takes over its live monsters
##   --scenario=separate  two clients stand on different maps; each owns its own, neither shares the other's monsters
##   --scenario=reconnect one client joins, drops, and a second connection of the same account is only accepted
##                        after the first one's lease is released
##   --scenario=version   a client that speaks another protocol is refused with a message that names both versions, and the
##                        account's play session is released so the player can try again after updating
##   --scenario=hostile   one client sends malformed, oversized, non-finite and flooding messages at the coordinator and
##                        must stay connected with a clean, bounded roster entry
## Prints `WORLD_PROBE PASS <user>` or `WORLD_PROBE FAIL <why>` (exit 1). The harness also scans the process log for
## script errors, so a handler that throws still fails the run.

var args := {}
var user := ""

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--") and arg.contains("="):
			args[arg.substr(2).get_slice("=", 0)] = arg.get_slice("=", 1)
	Game.save_slot = 99
	_run.call_deferred()

func _fail(message: String) -> void:
	print("WORLD_PROBE FAIL ", user, ": ", message)
	get_tree().quit(1)

func _wait_until(predicate: Callable, seconds := 30.0) -> bool:
	var deadline := Time.get_ticks_msec() + int(seconds * 1000)
	while Time.get_ticks_msec() < deadline:
		if predicate.call():
			return true
		await get_tree().create_timer(0.1, true).timeout
	return false

func _enter(map: StringName) -> Dictionary:
	Official.url = String(args.get("url", "https://127.0.0.1:18443"))
	Official.certificate_path = String(args.get("certificate", "res://server/official_ca.crt"))
	user = String(args.get("userid", "world_probe"))
	var result := await Official.authenticate("login" if args.get("resume", "0") == "1" else "register", user, "test-only-long-password-2026")
	if result.has("error"):
		return result
	var cid := ""
	if Official.characters.is_empty():
		var hero := Game.new_hero(&"knight", "World" + user.right(2))
		TempoRules.grant_starter(hero)
		result = await Official.add_character(hero, 0)
		if result.has("error"):
			return result
		cid = String(result.character.id)
	else:
		cid = String(Official.characters[0].id)
	result = await Official.begin_character(cid)
	if result.has("error"):
		return result
	Game.hero = HeroData.from_dict(result.save.hero)
	Game.save_slot = 99
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	await Game._begin_session(map, &"start" if map != &"sanctuary" else &"waypoint")
	var error := Net.join_game("127.0.0.1", int(result.get("game_port", 24690)))
	if error != "":
		return {"error": error}
	if not await _wait_until(func() -> bool: return Official.connected):
		return {"error": "Dedicated game handshake timed out: " + Net.last_error}
	return {}

func _leave() -> void:
	await Official.flush()
	await Game.end_session()
	print("WORLD_PROBE PASS ", user)
	get_tree().quit()

func _run() -> void:
	match String(args.get("scenario", "handoff")):
		"handoff":
			await _handoff()
		"separate":
			await _separate()
		"reconnect":
			await _reconnect()
		"hostile":
			await _hostile()
		"version":
			await _version()
		"bandwidth":
			await _bandwidth()
		_:
			_fail("unknown scenario")

# ---- handoff -------------------------------------------------------------------------------------------------------

func _handoff() -> void:
	var map := StringName(args.get("map", "ruined_forest"))
	var failure := await _enter(map)
	if failure.has("error"):
		_fail(String(failure.error))
		return
	if not await _wait_until(func() -> bool:
		return Net.player_count() == 2 and Net.world_owner(map) != 0 and Net.avatars().size() >= 1):
		_fail("the two heroes did not meet on %s (players %d, owner %d)" % [map, Net.player_count(), Net.world_owner(map)])
		return
	var owner_id := Net.world_owner(map)
	var epoch_before := Net._world_epoch
	if Net.is_world_authority():
		# this machine runs the monsters: give the other one a few checkpoints, then leave
		if not await _wait_until(func() -> bool: return Net._host_enemies.size() > 0, 20.0):
			_fail("the map owner has no registered monsters on %s" % map)
			return
		print("WORLD_PROBE OWNER ", user, " monsters=", Net._host_enemies.size(), " epoch=", epoch_before)
		await get_tree().create_timer(6.0, true).timeout
		_leave()
		return
	# this machine only shares the owner's monsters
	if owner_id == Net.my_id():
		_fail("neither owner nor member")
		return
	if not await _wait_until(func() -> bool: return Net._replicas.size() > 0 or not Net._worlds.get(String(map), {}).get("state", {}).is_empty(), 20.0):
		_fail("the member never received the owner's monsters or checkpoint")
		return
	var checkpoint: Dictionary = Net._worlds.get(String(map), {}).get("state", {})
	var expected := (checkpoint.get("enemies", []) as Array).size()
	print("WORLD_PROBE MEMBER ", user, " replicas=", Net._replicas.size(), " checkpoint_enemies=", expected)
	if not await _wait_until(func() -> bool: return Net.is_world_authority(), 40.0):
		_fail("the remaining hero never took over the map after its owner left")
		return
	if Net._world_epoch == epoch_before:
		_fail("the map kept its old generation after a hand-off")
		return
	if Net.player_count() != 1 or Net.world_owner(map) != Net.my_id():
		_fail("roster/ownership wrong after hand-off (players %d, owner %d)" % [Net.player_count(), Net.world_owner(map)])
		return
	# restored monsters register on the owner within a frame or two; report what the new owner ends up running
	var trail := []
	for step in 12:
		trail.append("%d/%d" % [Net._host_enemies.size(), get_tree().get_nodes_in_group(&"enemy").size()])
		if Net._host_enemies.size() > 0:
			break
		await get_tree().create_timer(0.25, true).timeout
	if expected > 0 and Net._host_enemies.size() == 0:
		_fail("the checkpoint had %d monsters but the new owner runs none (registered/in group: %s)" % [expected, ", ".join(trail)])
		return
	print("WORLD_PROBE HANDOFF ", user, " now runs ", Net._host_enemies.size(), " monsters (checkpoint ", expected, ") epoch ", Net._world_epoch)
	await get_tree().create_timer(2.0, true).timeout
	_leave()

# ---- separate maps -------------------------------------------------------------------------------------------------

func _separate() -> void:
	var map := StringName(args.get("map", "sanctuary"))
	var failure := await _enter(map)
	if failure.has("error"):
		_fail(String(failure.error))
		return
	if not await _wait_until(func() -> bool: return Net.player_count() == 2 and Net.world_owner(map) == Net.my_id(), 40.0):
		_fail("this hero does not own its own map %s (players %d, owner %d, me %d)" % [map, Net.player_count(), Net.world_owner(map), Net.my_id()])
		return
	# nobody else is on this map, so no avatar of the other player may exist here
	await get_tree().create_timer(4.0, true).timeout
	if not Net.avatars().is_empty():
		_fail("saw another player's avatar although they are on a different map")
		return
	var their_map := ""
	for id in Net.peers:
		if id != Net.my_id():
			their_map = String(Net.peers[id].get("map", ""))
	if their_map == "" or their_map == String(map):
		_fail("the other player's map is not known or not different (%s)" % their_map)
		return
	if Net._replicas.size() > 0:
		_fail("this machine holds replicas of monsters that belong to the other map")
		return
	print("WORLD_PROBE SEPARATE ", user, " owns ", map, "; other hero is on ", their_map)
	await get_tree().create_timer(float(args.get("hold", "6")), true).timeout
	_leave()

# ---- reconnect -----------------------------------------------------------------------------------------------------

func _reconnect() -> void:
	var failure := await _enter(&"sanctuary")
	if failure.has("error"):
		_fail(String(failure.error))
		return
	if not await _wait_until(func() -> bool: return Net.player_count() == 1, 20.0):
		_fail("did not enter the roster")
		return
	var cid := Official.character_id
	Game.hero.inventory.gold = 777
	if not await Official.flush():
		_fail("progress was not confirmed before the drop: " + Official.last_error)
		return
	# a second play request for the same account is refused while the first session holds the lease
	var again := await Official.request("/characters/play", {"character": cid})
	if String(again.get("code", "")) != "already_playing":
		_fail("a second play request was not refused while the first session was active: " + str(again))
		return
	# the connection is lost (no release, as with a dead network); the server keeps the lease for its short grace window
	Net._peer.close()
	await get_tree().create_timer(1.5, true).timeout
	again = await Official.request("/characters/play", {"character": cid})
	if String(again.get("code", "")) != "already_playing":
		_fail("the lease was handed out again during the grace window: " + str(again))
		return
	# the player returns to the menu (releases) and loads the character again
	await Official.release_character()
	var next := await Official.begin_character(cid)
	if next.has("error"):
		_fail("could not start again after release: " + String(next.error))
		return
	var restored := HeroData.from_dict(next.save.hero)
	if restored.inventory.gold != 777:
		_fail("the reconnected character lost its committed progress (gold %d)" % restored.inventory.gold)
		return
	Game.hero = restored
	Net.leave(false)
	var error := Net.join_game("127.0.0.1", int(next.get("game_port", 24690)))
	if error != "" or not await _wait_until(func() -> bool: return Official.connected, 30.0):
		_fail("could not rejoin the game server: " + error + Net.last_error)
		return
	print("WORLD_PROBE RECONNECT ", user, " progress kept; rejoined")
	_leave()

# ---- hostile --------------------------------------------------------------------------------------------------------

func _hostile() -> void:
	var failure := await _enter(&"sanctuary")
	if failure.has("error"):
		_fail(String(failure.error))
		return
	if not await _wait_until(func() -> bool: return Net.player_count() >= 1 and Net.peers.has(Net.my_id()), 20.0):
		_fail("did not enter the roster")
		return
	var me := Net.my_id()
	var honest_name := String(Net.peers[me].get("name", ""))
	# 1. oversized / mistyped profile updates and a second introduction
	Net._profile_changed.rpc_id(1, {"name": "X".repeat(5000), "level": 1e30, "junk": "j".repeat(40000)})
	Net._profile_changed.rpc_id(1, {"name": "Bounded Name That Is Far Too Long", "cls": "knight", "level": NAN, "map": "m".repeat(900), "extra": 1})
	Net._hello.rpc_id(1, Net.PROTOCOL, {"name": "again"})
	Net._hello.rpc_id(1, 1, {})
	# 2. map changes: unknown map, and a flood
	Net._in_map.rpc_id(1, "no_such_map")
	for i in 200:
		Net._in_map.rpc_id(1, "sanctuary")
	# 3. snapshots and effects with non-finite numbers, wrong types and huge sizes
	Net._allies.rpc("sanctuary", [5, "x", {"k": "p", "s": [Vector3(NAN, 0, 0), 0.0, Vector3.ZERO, 1.0, 1.0, true, "", 0, 1.0, false, false, 1]}])
	Net._allies.rpc("sanctuary", [{"k": "p", "s": "short"}])
	Net._appearances.rpc([{"k": "p", "a": {"blob": "b".repeat(60000)}}, 7, {"k": 5}])
	Net._remote_projectile.rpc("sanctuary", Vector3(NAN, 0, 0), Vector3.ZERO, INF, 0, "x".repeat(900), -1.0e9, 1.0e9)
	Net._remote_telegraph.rpc("sanctuary", Vector3(INF, 0, 0), 1.0e9, -5.0, Color.RED, "y".repeat(500), NAN)
	Net._remote_skill_fx.rpc("sanctuary", "veil", Vector3.ZERO, Vector3.ZERO, {"r": 1.0e9, "pad": "p".repeat(9000)})
	Net._remote_ping.rpc("sanctuary", Vector3(NAN, 0, 0), "Q".repeat(2000))
	# 4. a hit and a checkpoint that do not belong to this sender
	Net._client_hit.rpc("sanctuary", 1, 1, {"total": 9.9e30}, Vector3(NAN, 0, 0), "p")
	Net._world_checkpoint.rpc("sanctuary", 1, {"blob": "c".repeat(900000)})
	# 5. chat flood
	for i in 300:
		Net._chat.rpc("flood %d" % i)
	for i in 100:
		Net._allies.rpc("sanctuary", _filler_pack())
	await get_tree().create_timer(3.0, true).timeout
	if not Official.connected or not Net.is_active():
		_fail("the coordinator dropped a client that only sent bad data, or it is no longer connected: " + Net.last_error)
		return
	var entry: Dictionary = Net.peers.get(me, {})
	if entry.is_empty():
		_fail("this player is no longer on the roster")
		return
	var name_now := String(entry.get("name", ""))
	if name_now.length() > 18 or name_now == "":
		_fail("the roster holds an unbounded name (%d characters)" % name_now.length())
		return
	if not (entry.get("map", "") as String).length() <= 64 or entry.has("junk") or entry.has("extra"):
		_fail("the roster kept data it should not: " + str(entry.keys()))
		return
	if int(entry.get("level", 0)) < 1 or int(entry.get("level", 0)) > BH.LEVEL_CAP:
		_fail("the roster holds an impossible level %s" % str(entry.get("level")))
		return
	var health := await Official.check_server()
	if health.has("error") or not bool(health.get("game_online", false)):
		_fail("the coordinator is not healthy after bad input: " + str(health))
		return
	print("WORLD_PROBE HOSTILE ", user, " survived; roster name '", name_now, "' (honest '", honest_name, "')")
	_leave()

## Everyone stands on one real map with its monsters and the traffic of this machine's ENet host is read over `--hold` seconds.
## `--expected` is how many clients take part; the first to arrive on the map runs its monsters (and sends their snapshots).
func _bandwidth() -> void:
	var map := StringName(args.get("map", "ruined_forest"))
	var failure := await _enter(map)
	if failure.has("error"):
		_fail(String(failure.error))
		return
	var expected := int(args.get("expected", "2"))
	if not await _wait_until(func() -> bool: return Net.player_count() == expected and Net.avatars().size() >= expected - 1, 90.0):
		_fail("only %d of %d heroes met (avatars %d)" % [Net.player_count(), expected, Net.avatars().size()])
		return
	await get_tree().create_timer(5.0, true).timeout
	Net.pop_traffic()
	var hold := float(args.get("hold", "30"))
	await get_tree().create_timer(hold, true).timeout
	var t := Net.pop_traffic()
	print("BANDWIDTH ", user, " role=", "map-owner" if Net.is_world_authority() else "member", " players=", expected, " monsters=", Net._host_enemies.size() if Net.is_world_authority() else Net._replicas.size(),
		" sent_kbps=%.1f received_kbps=%.1f over=%.0fs" % [t.sent * 8.0 / 1000.0 / t.seconds, t.received * 8.0 / 1000.0 / t.seconds, t.seconds])
	_leave()

func _version() -> void:
	# sign in and take a play session, but introduce this client as an older game
	Official.url = String(args.get("url", "https://127.0.0.1:18443"))
	Official.certificate_path = String(args.get("certificate", "res://server/official_ca.crt"))
	user = String(args.get("userid", "version_probe"))
	var result := await Official.authenticate("register", user, "test-only-long-password-2026")
	if result.has("error"):
		_fail(String(result.error))
		return
	var hero := Game.new_hero(&"knight", "Vers" + user.right(2))
	TempoRules.grant_starter(hero)
	result = await Official.add_character(hero, 0)
	if result.has("error"):
		_fail(String(result.error))
		return
	var cid := String(result.character.id)
	result = await Official.begin_character(cid)
	if result.has("error"):
		_fail(String(result.error))
		return
	Game.hero = HeroData.from_dict(result.save.hero)
	Game.current_map_id = &"sanctuary"
	Game.in_session = true
	Net.protocol_override = Net.PROTOCOL - 1
	var error := Net.join_game("127.0.0.1", int(result.get("game_port", 24690)))
	if error != "":
		_fail(error)
		return
	if not await _wait_until(func() -> bool: return not Net.is_active() and Net.last_error != "", 20.0):
		_fail("the old game was not turned away (connected=%s, error='%s')" % [Official.connected, Net.last_error])
		return
	if not Net.last_error.contains(str(Net.PROTOCOL)) or not Net.last_error.contains(str(Net.PROTOCOL - 1)):
		_fail("the refusal does not name both versions: " + Net.last_error)
		return
	if Official.connected:
		_fail("an older game ended up connected")
		return
	Net.protocol_override = -1
	print("WORLD_PROBE VERSION ", user, " refused: ", Net.last_error)
	await Official.release_character()
	var again := await Official.request("/characters/play", {"character": cid})
	if again.has("error"):
		_fail("the play session was not released after the refusal: " + String(again.error))
		return
	await Official.request("/characters/release", {"character": cid, "lease": String(again.lease)})
	print("WORLD_PROBE PASS ", user)
	get_tree().quit()

func _filler_pack() -> Array:
	return [{"k": "p", "s": [Vector3(1, 0, 1), 0.0, Vector3.ZERO, 10.0, 10.0, true, "", 0, 1.0, false, false, 1]}]
