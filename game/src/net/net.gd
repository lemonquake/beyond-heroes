extends Node
## Multiplayer (autoload `Net`, bh-008). Co-op for up to four heroes over ENet, the same on PC and Android.
##
##   Host      a player opens their running game ("Host Game"). Their machine is the authority for the world: it runs
##             the monsters, decides where the party is, and relays everyone's snapshots.
##   Join      another player, already playing their own hero, joins by LAN discovery or by address. Their game
##             follows the host to the host's map and shows the host's monsters as replicas.
##   Heroes    every machine sends its own hero and Tempos ~15 times a second; the others draw them as NetAvatars.
##   Combat    a client's blow on a replica is resolved on the client (its hero's stats) and the result is applied by
##             the host; a monster's blow on a NetAvatar is sent to the avatar's owner and resolved against the real
##             hero there (guard, dodge, resistances all count). Kills are announced; every hero in the map gets the
##             experience and rolls their own loot (instanced loot: nobody steals anybody's drops).
##   Travel    the party follows the host: when the host changes maps the clients load the same map. Clients cannot
##             take doors or waypoints on their own while connected.
##   Chat      the chat box is shared.
## Everything else (inventory, shops, crafting, dialogue, saving) stays per player, on their own machine.

signal state_changed
signal peers_changed
signal lan_games_changed

const PROTOCOL := 2                  # 2 (bh-010): Ranger / Shadowblade, auras, shared skill effects
const PORT := 24680
const DISCOVERY_PORT := 24681
const MAX_CLIENTS := 3
const ALLY_RATE := 15.0
const ENEMY_RATE := 12.0
const ENEMY_RANGE := 70.0            # monsters farther than this from a client's hero are not streamed to it
const APPEARANCE_EVERY := 30         # full appearance every N ally snapshots (and whenever gear changes)
const GONE_AFTER := 4.0

enum Mode { OFFLINE, HOST, CLIENT }

var mode := Mode.OFFLINE
var connecting := false
var peers := {}                      # peer id -> {name, cls, level, map}
var lan_games := {}                  # "ip" -> {name, host, map, players, port, t}
var last_error := ""
var protocol_override := -1          # probes only: pretend to be another game version
var following := false               # a client is loading the host's map: its own travel rules are lifted

var _peer: ENetMultiplayerPeer
var _udp: PacketPeerUDP              # host: broadcaster
var _listen: PacketPeerUDP           # anyone: discovery listener
var _bcast_t := 0.0
var _ally_t := 0.0
var _enemy_t := 0.0
var _ally_count := 0
var _next_eid := 1
var _host_enemies := {}              # host: eid -> Enemy
var _known := {}                     # host: peer -> {eid: true} spawn infos already sent
var _replicas := {}                  # client: eid -> Enemy
var _replica_seen := {}              # client: eid -> time of the last snapshot that carried it
var _avatars := {}                   # "peer:key" -> NetAvatar
var _app_sig := {}                   # local ally key -> appearance hash (resend on change)
var _unloading := false              # the old map is leaving the tree: its monsters are not "gone", the map is

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)
	get_tree().node_added.connect(_on_node_added)
	Events.actor_died.connect(_on_actor_died)
	Game.session_ended.connect(func() -> void:
		if is_active():
			leave(false))

# ---- State --------------------------------------------------------------------------------------------------------

func is_active() -> bool:
	return mode != Mode.OFFLINE

func is_host() -> bool:
	return mode == Mode.HOST

func is_client() -> bool:
	return mode == Mode.CLIENT

func my_id() -> int:
	return multiplayer.get_unique_id() if is_active() else 1

## Each human player's colour: their name plate, foot ring, chat name and party entry (bh-008).
const PLAYER_COLORS := [Color(1.0, 0.78, 0.3), Color(0.35, 0.8, 1.0), Color(0.55, 1.0, 0.45), Color(1.0, 0.45, 0.75)]

func player_color(peer: int) -> Color:
	var ids := peers.keys()
	ids.sort()
	var i := ids.find(peer)
	return PLAYER_COLORS[(i if i >= 0 else absi(peer)) % PLAYER_COLORS.size()]

func player_count() -> int:
	return peers.size()

func _profile() -> Dictionary:
	var h: HeroData = Game.hero
	return {"name": h.hero_name if h else "Hero", "cls": String(h.cls.id) if h else "knight",
		"level": h.progress.level if h else 1, "map": String(Game.current_map_id),
		"device": "Mobile" if Settings.is_mobile_device() else "PC"}

# ---- Host / join / leave ------------------------------------------------------------------------------------------

## Open this running game to others. Returns "" or an error to show.
func host_game(port := PORT) -> String:
	if is_active():
		return "Already connected."
	if not Game.in_session:
		return "Start or continue a game first."
	_peer = ENetMultiplayerPeer.new()
	var err := _peer.create_server(port, MAX_CLIENTS)
	if err != OK:
		_peer = null
		return "Could not open port %d (error %d). Is another game using it?" % [port, err]
	multiplayer.multiplayer_peer = _peer
	mode = Mode.HOST
	peers = {1: _profile()}
	_known.clear()
	_host_enemies.clear()
	_next_eid = 1
	_register_existing_enemies()
	_start_broadcast()
	Events.notify.emit("Your world is open. Others can join from Multiplayer > Join.", &"info")
	_chat_system("%s opened the world to other heroes." % peers[1].name)
	state_changed.emit()
	peers_changed.emit()
	return ""

## Join a hosted game at `address` (a room code, an IP or a host name). Returns "" or an error; the result arrives later.
func join_game(address: String, port := PORT) -> String:
	if is_active():
		return "Already connected."
	if not Game.in_session:
		return "Start or continue a game first, then join."
	address = address.strip_edges()
	if address == "":
		return "Type the host's room code."
	var code := NetCodec.parse_room_code(address, PORT)
	if not code.is_empty() and not address.contains("."):
		address = code[0]
		port = code[1]
	_peer = ENetMultiplayerPeer.new()
	var err := _peer.create_client(address, port)
	if err != OK:
		_peer = null
		return "Could not reach %s (error %d)." % [address, err]
	multiplayer.multiplayer_peer = _peer
	mode = Mode.CLIENT
	connecting = true
	last_error = ""
	state_changed.emit()
	return ""

## Leave the party (or close the hosted world). A client's world becomes its own again: the map reloads with its
## own monsters.
func leave(reload := true) -> void:
	var was_client := is_client()
	if is_active() and _peer:
		if is_host():
			_chat_system("The host closed the world.")
		_peer.close()
	multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	_peer = null
	mode = Mode.OFFLINE
	connecting = false
	following = false
	peers.clear()
	_known.clear()
	_host_enemies.clear()
	_stop_broadcast()
	_clear_avatars()
	_clear_replicas()
	state_changed.emit()
	peers_changed.emit()
	if was_client and reload and Game.in_session:
		Game.reload_current_map()

func _on_peer_connected(_id: int) -> void:
	pass                                     # the client introduces itself with _hello

func _on_peer_disconnected(id: int) -> void:
	if not is_active():
		return
	var who: String = peers.get(id, {}).get("name", "A hero")
	peers.erase(id)
	_known.erase(id)
	_remove_avatars_of(id)
	if is_host():
		_chat_system("%s left." % who)
		_rpc_peers()
	peers_changed.emit()

func _on_connected() -> void:
	connecting = false
	_hello.rpc_id(1, protocol_override if protocol_override >= 0 else PROTOCOL, _profile())

func _on_connection_failed() -> void:
	last_error = "Could not connect to the host."
	Events.notify.emit(last_error, &"error")
	leave(false)

func _on_server_disconnected() -> void:
	Events.notify.emit("The host closed the world. You are playing alone again.", &"info")
	leave(true)

@rpc("any_peer", "reliable")
func _hello(proto: int, profile: Dictionary) -> void:
	if not is_host():
		return
	var id := multiplayer.get_remote_sender_id()
	if proto != PROTOCOL:
		_rejected.rpc_id(id, "Different game versions (host %d, you %d). Update both games." % [PROTOCOL, proto])
		get_tree().create_timer(0.5).timeout.connect(func() -> void:
			if _peer:
				_peer.disconnect_peer(id))
		return
	peers[id] = profile
	_known[id] = {}
	var p := Game.player as Node3D
	_welcome.rpc_id(id, {"map": String(Game.current_map_id), "pos": p.global_position if p else Vector3.ZERO,
		"yaw": p.rotation.y if p else 0.0, "peers": peers})
	_chat_system("%s joined (%s)." % [profile.get("name", "A hero"), profile.get("device", "PC")])
	_rpc_peers()
	peers_changed.emit()

@rpc("authority", "reliable")
func _rejected(why: String) -> void:
	last_error = why
	Events.notify.emit(why, &"error")
	leave(false)

@rpc("authority", "reliable")
func _welcome(info: Dictionary) -> void:
	peers = info.get("peers", {})
	Events.notify.emit("Joined %s's world." % peers.get(1, {}).get("name", "the host"), &"info")
	state_changed.emit()
	peers_changed.emit()
	_follow(StringName(info.map), info.pos, float(info.yaw))

func _rpc_peers() -> void:
	_peers_update.rpc(peers)

@rpc("authority", "reliable")
func _peers_update(p: Dictionary) -> void:
	peers = p
	peers_changed.emit()

# ---- Following the host between maps ------------------------------------------------------------------------------

## Game.load_map calls these around every map swap on this machine.
func map_unloading() -> void:
	_unloading = true

func on_local_map_loaded(id: StringName) -> void:
	_unloading = false
	if not is_active():
		return
	_clear_avatars()
	_clear_replicas()
	if is_host():
		peers[1] = _profile()
		for pid in _known:
			_known[pid] = {}
		_register_existing_enemies()
		var p := Game.player as Node3D
		_host_moved.rpc(String(id), p.global_position if p else Vector3.ZERO, p.rotation.y if p else 0.0)
		_rpc_peers()
	elif not following:
		_in_map.rpc_id(1, String(id))      # while following, _follow reports once the map is ready

@rpc("authority", "reliable")
func _host_moved(map: String, pos: Vector3, yaw: float) -> void:
	_follow(StringName(map), pos, yaw)

func _follow(map: StringName, pos: Vector3, yaw: float) -> void:
	following = true
	await Game.net_follow(map, pos, yaw)
	following = false
	if is_client():
		_in_map.rpc_id(1, String(Game.current_map_id))   # now the host may stream its monsters

@rpc("any_peer", "reliable")
func _in_map(map: String) -> void:
	if not is_host():
		return
	var id := multiplayer.get_remote_sender_id()
	if peers.has(id):
		peers[id]["map"] = map
	_known[id] = {}
	_rpc_peers()

## May this machine take a door, a waypoint or a portal right now? (Clients follow the host.)
func may_travel() -> bool:
	if is_client() and not following:
		Events.notify.emit("The party follows %s. Only the host can lead it elsewhere." % peers.get(1, {}).get("name", "the host"), &"locked")
		return false
	return true

func _peer_map(id: int) -> String:
	return String(peers.get(id, {}).get("map", ""))

# ---- LAN discovery ------------------------------------------------------------------------------------------------

func _start_broadcast() -> void:
	_udp = PacketPeerUDP.new()
	_udp.set_broadcast_enabled(true)
	_udp.set_dest_address("255.255.255.255", DISCOVERY_PORT)
	_bcast_t = 0.0

func _stop_broadcast() -> void:
	if _udp:
		_udp.close()
	_udp = null

## Listen for hosts on the local network (the Join list). Harmless to call repeatedly.
func start_discovery() -> void:
	if _listen:
		return
	_listen = PacketPeerUDP.new()
	if _listen.bind(DISCOVERY_PORT) != OK:
		_listen = null
		last_error = "Cannot listen for local games (port %d busy)." % DISCOVERY_PORT

func stop_discovery() -> void:
	if _listen:
		_listen.close()
	_listen = null
	lan_games.clear()

func _broadcast() -> void:
	if _udp == null:
		return
	var h := Game.hero
	var msg := {"bh": PROTOCOL, "host": h.hero_name if h else "Host", "level": h.progress.level if h else 1,
		"map": String(DB.map_def(Game.current_map_id).display_name) if DB.map_def(Game.current_map_id) else "", "players": peers.size(),
		"max": MAX_CLIENTS + 1, "port": PORT}
	_udp.put_packet(JSON.stringify(msg).to_utf8_buffer())

func _poll_discovery() -> void:
	if _listen == null:
		return
	var changed := false
	while _listen.get_available_packet_count() > 0:
		var pkt := _listen.get_packet()
		var ip := _listen.get_packet_ip()
		var d = JSON.parse_string(pkt.get_string_from_utf8())
		if d is Dictionary and d.has("bh"):
			d["t"] = Time.get_ticks_msec()
			d["ip"] = ip
			changed = changed or not lan_games.has(ip)
			lan_games[ip] = d
	var now := Time.get_ticks_msec()
	for ip in lan_games.keys():
		if now - int(lan_games[ip].t) > 4000:
			lan_games.erase(ip)
			changed = true
	if changed:
		lan_games_changed.emit()

## This machine's local addresses (to tell a friend what to type).
## This machine's room codes: [[label, code, address]] — the home network first, then a LAN VPN (Radmin-style 26.x).
static func room_codes(port := PORT) -> Array:
	var out := []
	for a in local_addresses():
		var label := "VPN" if a.begins_with("26.") or a.begins_with("25.") else "Home network"
		out.append([label, NetCodec.room_code(a, port, PORT), a])
	out.sort_custom(func(x, y): return x[0] == "Home network" and y[0] != "Home network")
	return out

static func local_addresses() -> PackedStringArray:
	var out := PackedStringArray()
	for a in IP.get_local_addresses():
		if a.count(".") == 3 and not a.begins_with("127.") and not a.begins_with("169.254."):
			out.append(a)
	return out

# ---- Frame loop ---------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	_poll_discovery()
	if not is_active():
		return
	if is_host():
		_bcast_t -= delta
		if _bcast_t <= 0.0:
			_bcast_t = 1.0
			_broadcast()
	if connecting or not Game.in_session or Game.travelling or following:
		return
	_ally_t -= delta
	if _ally_t <= 0.0:
		_ally_t = 1.0 / ALLY_RATE
		_send_allies()
	if is_host():
		_enemy_t -= delta
		if _enemy_t <= 0.0:
			_enemy_t = 1.0 / ENEMY_RATE
			_send_enemies()
	else:
		_expire_replicas()

# ---- Allies (heroes and Tempos) -----------------------------------------------------------------------------------

func _local_allies() -> Array:
	var out := []
	if Game.player is Player and is_instance_valid(Game.player):
		out.append(["p", Game.player])
	for t in get_tree().get_nodes_in_group(&"tempo"):
		if t is Tempo and t.data and is_instance_valid(t):
			out.append(["t%d" % t.data.uid, t])
	return out

static func actor_state(a: Actor) -> Array:
	var v := a.visual
	var act := v.current_action() if v else &""
	return [a.global_position, a.rotation.y, a.velocity, a.hp, a.max_hp(), a.alive, String(act),
		v.action_serial if v else 0, v.action_rate if v else 1.0, bool(v._action_loop) if v else false, a.in_combat(), a.level]

func _send_allies() -> void:
	_ally_count += 1
	var pack := []
	for pair in _local_allies():
		var a: Actor = pair[1]
		var e := {"k": pair[0], "s": actor_state(a), "n": a.display_name}
		if a is Tempo:
			e["n"] = (a as Tempo).data.tempo_name
		if a.visual:
			var sig := hash(str(a.visual.appearance)) ^ hash(String(a.visual._stance_idle))
			if _ally_count % APPEARANCE_EVERY == 1 or _app_sig.get(pair[0], 0) != sig:
				_app_sig[pair[0]] = sig
				var app := a.visual.appearance.duplicate(true)
				app["stance"] = String(a.visual._stance_idle)
				e["a"] = app
		pack.append(e)
	_allies.rpc(String(Game.current_map_id), pack)

@rpc("any_peer", "unreliable_ordered")
func _allies(map: String, pack: Array) -> void:
	var from := multiplayer.get_remote_sender_id()
	if peers.has(from):
		peers[from]["map"] = map
	if not Game.in_session or Game.current_map == null or Game.travelling or following:
		return
	if map != String(Game.current_map_id):
		_remove_avatars_of(from)
		return
	var seen := {}
	for e in pack:
		var k := "%d:%s" % [from, e.k]
		seen[k] = true
		var av: NetAvatar = _avatars.get(k)
		if av == null or not is_instance_valid(av):
			if not e.has("a"):
				continue                       # wait for the appearance
			var s: Array = e.s
			av = NetAvatar.new().setup(from, String(e.k), {"name": e.get("n", "Hero"), "lvl": s[11], "mhp": s[4], "hp": s[3]})
			Game.current_map.add_child(av)
			av.snap_to(s[0], s[1])
			_avatars[k] = av
		if e.has("a"):
			av.set_appearance(e.a)
		av.display_name = String(e.get("n", av.display_name))
		av.apply_state(e.s)
	for k in _avatars.keys():
		if k.begins_with("%d:" % from) and not seen.has(k):
			_free_avatar(k)

func _free_avatar(k: String) -> void:
	var av = _avatars.get(k)
	if av and is_instance_valid(av):
		av.queue_free()
	_avatars.erase(k)

func _remove_avatars_of(peer: int) -> void:
	for k in _avatars.keys():
		if k.begins_with("%d:" % peer):
			_free_avatar(k)

func _clear_avatars() -> void:
	for k in _avatars.keys():
		_free_avatar(k)
	_avatars.clear()

func avatar(peer: int, key := "p") -> NetAvatar:
	var av = _avatars.get("%d:%s" % [peer, key])
	return av if av and is_instance_valid(av) else null

## Other players' heroes on this map (HUD party list, auto-aim ignores them).
func avatars() -> Array:
	var out := []
	for k in _avatars:
		if is_instance_valid(_avatars[k]):
			out.append(_avatars[k])
	return out

# ---- Host: monsters -----------------------------------------------------------------------------------------------

func _on_node_added(n: Node) -> void:
	if is_host() and n is Enemy and not (n as Enemy).net_replica:
		_register_enemy.call_deferred(n)

func _register_existing_enemies() -> void:
	if Game.current_map == null:
		return
	for e in get_tree().get_nodes_in_group(&"enemy"):     # find_children cannot match script classes
		if e is Enemy and Game.current_map.is_ancestor_of(e):
			_register_enemy(e)

func _register_enemy(e: Enemy) -> void:
	if not is_instance_valid(e) or e.has_meta(&"net_id") or not e.is_inside_tree():
		return
	var id := _next_eid
	_next_eid += 1
	e.set_meta(&"net_id", id)
	_host_enemies[id] = e
	e.tree_exiting.connect(func() -> void:
		_host_enemies.erase(id)
		if is_host() and e.alive and not _unloading:
			_enemy_gone.rpc(id))

static func enemy_info(e: Enemy) -> Dictionary:
	return {"id": int(e.get_meta(&"net_id")), "def": String(e.def.id), "lvl": e.level, "mods": e.elite_mods.map(func(m): return String(m)),
		"diff": Game.difficulty, "mb": String(e.miniboss.get("id", "")), "flag": String(e.get_meta(&"boss_flag", "")),
		"pos": e.global_position, "yaw": e.rotation.y, "hp": e.hp}

func _send_enemies() -> void:
	var here := String(Game.current_map_id)
	for pid in peers:
		if pid == 1 or _peer_map(pid) != here:
			continue
		var av := avatar(pid)
		var center: Vector3 = av.global_position if av else (Game.player as Node3D).global_position
		var known: Dictionary = _known.get_or_add(pid, {})
		var infos := []
		var states := []
		for id in _host_enemies:
			var e: Enemy = _host_enemies[id]
			if not is_instance_valid(e) or not e.alive:
				continue
			if e.global_position.distance_to(center) > ENEMY_RANGE:
				continue
			if not known.has(id):
				known[id] = true
				infos.append(enemy_info(e))
			var v := e.visual
			states.append([id, e.global_position, e.rotation.y, e.velocity, e.hp, e.max_hp(), String(v.current_action() if v else &""),
				v.action_serial if v else 0, v.action_rate if v else 1.0, bool(v._action_loop) if v else false, e.brain.is_engaged(), e.shield_hp])
		if not infos.is_empty():
			_enemy_spawn.rpc_id(pid, infos)
		if not states.is_empty():
			_enemy_states.rpc_id(pid, states)

func _on_actor_died(actor: Node, killer: Node) -> void:
	if not is_host() or not (actor is Enemy) or not actor.has_meta(&"net_id"):
		return
	var kp := 0
	if killer is NetAvatar:
		kp = (killer as NetAvatar).owner_peer
	elif killer is Player or killer is Tempo:
		kp = 1
	var e := actor as Enemy
	var here := String(Game.current_map_id)
	for pid in peers:
		if pid != 1 and _peer_map(pid) == here and _known.get(pid, {}).has(int(e.get_meta(&"net_id"))):
			_enemy_died.rpc_id(pid, int(e.get_meta(&"net_id")), kp, String(e.death_clip()))

## A client's hit on one of the host's monsters: the client resolved it (its hero, its skills); apply the numbers.
@rpc("any_peer", "reliable")
func _client_hit(eid: int, res: Dictionary, hit_point: Vector3, key: String) -> void:
	if not is_host():
		return
	var e: Enemy = _host_enemies.get(eid)
	if e == null or not is_instance_valid(e) or not e.alive:
		return
	var from := multiplayer.get_remote_sender_id()
	var av := avatar(from, key)
	if av == null:
		av = avatar(from, "p")
	var result := NetCodec.decode_result(res)
	var req := DamageRequest.new()
	req.attacker = av.stats if av else null
	req.heavy = result.heavy
	req.tags = res.get("tags", {})
	e.ensure_stats()
	e._apply_result(result, req, av, hit_point)

## A monster hit a NetAvatar here on the host: the owner resolves it against the real hero or Tempo.
func forward_ally_hit(av: NetAvatar, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if not is_host():
		return
	var src: Node = attacker
	if not (src is Enemy):
		return                                 # traps and hazards exist on the owner's map too: no double hits
	_ally_hit.rpc_id(av.owner_peer, av.key, NetCodec.encode_request(req), int(src.get_meta(&"net_id", 0)), hit_point)

# ---- Client: replicas ---------------------------------------------------------------------------------------------

@rpc("authority", "reliable")
func _enemy_spawn(infos: Array) -> void:
	if not is_client() or Game.current_map == null or following:
		return
	for info in infos:
		var id := int(info.id)
		if _replicas.has(id) and is_instance_valid(_replicas[id]):
			continue
		var edef := DB.enemy(StringName(info.def))
		if edef == null:
			continue
		var e := Enemy.new()
		e.net_replica = true
		var diff: Dictionary = DataEnemies.DIFFICULTY[clampi(int(info.diff), 0, DataEnemies.DIFFICULTY.size() - 1)]
		e.setup(edef, int(info.lvl), (info.mods as Array).map(func(m): return StringName(m)), diff)
		if String(info.mb) != "":
			var md := DataMinibosses.find(StringName(info.mb))
			if not md.is_empty():
				e.make_miniboss(md)
		if String(info.flag) != "":
			e.set_meta(&"boss_flag", StringName(info.flag))
		e.set_meta(&"net_id", id)
		e.name = "Replica_%d" % id
		Game.current_map.add_child(e)
		e.global_position = info.pos
		e.rotation.y = float(info.yaw)
		e.net_snap(info.pos, float(info.yaw))
		e.hp = float(info.hp)
		_replicas[id] = e
		_replica_seen[id] = Time.get_ticks_msec() * 0.001

@rpc("authority", "unreliable_ordered")
func _enemy_states(states: Array) -> void:
	if not is_client() or following:
		return
	var now := Time.get_ticks_msec() * 0.001
	for s in states:
		var e: Enemy = _replicas.get(int(s[0]))
		if e and is_instance_valid(e):
			e.net_apply(s)
			_replica_seen[int(s[0])] = now

@rpc("authority", "reliable")
func _enemy_died(eid: int, killer_peer: int, clip: String) -> void:
	var e: Enemy = _replicas.get(eid)
	if e == null or not is_instance_valid(e) or not e.alive:
		return
	var killer: Node = null
	if killer_peer == my_id():
		killer = Game.player
	elif killer_peer != 0:
		killer = avatar(killer_peer)
	e.net_die(killer, StringName(clip))
	_replicas.erase(eid)

@rpc("authority", "reliable")
func _enemy_gone(eid: int) -> void:
	var e: Enemy = _replicas.get(eid)
	if e and is_instance_valid(e) and e.alive:
		e.queue_free()
	_replicas.erase(eid)

func _expire_replicas() -> void:
	# monsters that walked out of streaming range keep their last pose; far-away stale ones are dropped
	var now := Time.get_ticks_msec() * 0.001
	for id in _replicas.keys():
		var e: Enemy = _replicas[id]
		if not is_instance_valid(e):
			_replicas.erase(id)
		elif now - float(_replica_seen.get(id, now)) > GONE_AFTER and Game.player and e.global_position.distance_to((Game.player as Node3D).global_position) > ENEMY_RANGE * 0.8:
			e.queue_free()
			_replicas.erase(id)
			_forget_on_host.rpc_id(1, id)

@rpc("any_peer", "reliable")
func _forget_on_host(eid: int) -> void:
	# the client dropped a far replica: send its spawn info again when it comes back into range
	var from := multiplayer.get_remote_sender_id()
	if is_host() and _known.has(from):
		(_known[from] as Dictionary).erase(eid)

func _clear_replicas() -> void:
	for id in _replicas:
		if is_instance_valid(_replicas[id]):
			_replicas[id].queue_free()
	_replicas.clear()
	_replica_seen.clear()

## A local hero or Tempo hit a replica: show it here, let the host apply it.
func replica_hit(e: Enemy, result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if not is_client() or not e.has_meta(&"net_id"):
		return
	var key := "p"
	if attacker is Tempo and (attacker as Tempo).data:
		key = "t%d" % (attacker as Tempo).data.uid
	var d := NetCodec.encode_result(result)
	d["tags"] = {&"push_dir": req.tags.get(&"push_dir", Vector3.ZERO), &"launch": req.tags.get(&"launch", 0.0)}
	_client_hit.rpc_id(1, int(e.get_meta(&"net_id")), d, hit_point if hit_point.is_finite() else e.center(), key)

## The host says a monster hit one of this machine's allies: resolve it against the real one.
@rpc("authority", "reliable")
func _ally_hit(key: String, req_d: Dictionary, attacker_eid: int, hit_point: Vector3) -> void:
	if not Game.in_session:
		return
	var target: Actor = null
	for pair in _local_allies():
		if pair[0] == key:
			target = pair[1]
	if target == null or not target.alive:
		return
	var src: Enemy = _replicas.get(attacker_eid)
	var req := NetCodec.decode_request(req_d)
	if src and is_instance_valid(src):
		src.ensure_stats()
		req.attacker = src.stats
	else:
		var st := DerivedStats.new()
		st.level = target.level
		req.attacker = st
	target.receive_hit(req, src if src and is_instance_valid(src) else null, hit_point if hit_point.is_finite() else Vector3.INF)

## A Knight's aura pulse reached another player's hero or Tempo (bh-010): the owner applies the aura's status and stat
## bonuses to its real actor, like the Knight's own Tempos get them. Only the aura id and the numbers travel.
func send_aura(av: NetAvatar, sid: StringName, time: float, mag: float, mods: Array, p: Dictionary, eff: float) -> void:
	if not is_active() or av == null or not is_instance_valid(av):
		return
	var vals := []
	for m in mods:
		vals.append(float(p.get(String(m[2]), 0.0)) * float(m[3]) * eff)
	_ally_aura.rpc_id(av.owner_peer, av.key, String(sid), time, mag, vals)

@rpc("any_peer", "unreliable")
func _ally_aura(key: String, sid: String, time: float, mag: float, vals: Array) -> void:
	if not Game.in_session:
		return
	var s := DB.skill(StringName(sid))
	if s == null or not s.is_aura() or vals.size() != s.aura_mods.size():
		return
	for pair in _local_allies():
		if pair[0] != key or not (pair[1] as Actor).alive:
			continue
		var mods: Array = []
		for i in s.aura_mods.size():
			var m: Array = s.aura_mods[i]
			mods.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, clampf(float(vals[i]), -5.0, 5.0), s.display_name))
		(pair[1] as Actor).status.apply(s.id, clampf(time, 0.0, 5.0), clampf(mag, 0.0, 2.0), 0.0, Elements.PHYSICAL, mods)

## Round-trip time to a peer in ms (the host sees every client; a client sees the host). -1 when unknown.
func ping_ms(peer: int) -> int:
	if _peer == null or not is_active():
		return -1
	var target := peer if is_host() else 1
	if target == my_id():
		return 0
	var pp := _peer.get_peer(target)
	return int(pp.get_statistic(ENetPacketPeer.PEER_ROUND_TRIP_TIME)) if pp else -1

# ---- Shared effects (projectiles and ground warnings) -------------------------------------------------------------

## Projectile.spawn / AreaEffects.delayed report what this machine is authoritative for (its own hero and Tempos;
## the host also its monsters); the others draw harmless copies.
func owns_source(source: Node) -> bool:
	if source == null or not is_instance_valid(source):
		return false
	if source is NetAvatar:
		return false
	if source is Enemy:
		return is_host() and not (source as Enemy).net_replica
	return source is Player or source is Tempo

func share_projectile(p: Projectile, from: Vector3, dir: Vector3, speed: float, element: int, look: String) -> void:
	if not is_active() or not owns_source(p.source):
		return
	_fx_projectile.call_deferred(p, from, dir, speed, element, look)

func _fx_projectile(p: Projectile, from: Vector3, dir: Vector3, speed: float, element: int, look: String) -> void:
	if not is_instance_valid(p):
		return
	_remote_projectile.rpc(String(Game.current_map_id), from, dir, speed, element, look, p.max_range, p.radius)

@rpc("any_peer", "unreliable")
func _remote_projectile(map: String, from: Vector3, dir: Vector3, speed: float, element: int, look: String, reach: float, radius: float) -> void:
	if map != String(Game.current_map_id) or FX.world == null or Game.travelling:
		return
	var p := Projectile.spawn(FX.world, from, dir, speed, null, null, 0, element, look)
	p.max_range = reach
	p.radius = radius

## Persistent skill effects (bh-010): Hallowed Hammer spirals, Blizzard / Arrow Rain, sentinels, traps and Smoke Veil.
## Other machines draw harmless copies (no damage request); hits stay with the caster's machine.
func share_skill_fx(kind: String, at: Vector3, dir: Vector3, extra: Dictionary) -> void:
	if not is_active():
		return
	_remote_skill_fx.rpc(String(Game.current_map_id), kind, at, dir, extra)

@rpc("any_peer", "unreliable")
func _remote_skill_fx(map: String, kind: String, at: Vector3, dir: Vector3, extra: Dictionary) -> void:
	if map != String(Game.current_map_id) or FX.world == null or Game.travelling:
		return
	match kind:
		"spiral":
			var h := SpiralHammer.create(FX.world, at, atan2(dir.z, dir.x), null, null, 0, float(extra.get("d", 2.2)))
			h.growth = float(extra.get("g", 1.9))
		"storm":
			StormArea.create(FX.world, at, float(extra.get("r", 4.0)), float(extra.get("d", 3.0)), float(extra.get("t", 0.5)), null, null, 0, String(extra.get("s", "ice")))
		"sentry":
			SkillSentry.create(FX.world, at, String(extra.get("m", "turret")), null, null, 0, float(extra.get("l", 8.0)), float(extra.get("i", 0.8)),
				float(extra.get("r", 14.0)), int(extra.get("e", 0)), 99)
		"trap":
			SkillTrap.create(FX.world, at, String(extra.get("s", "snare")), null, null, 0, float(extra.get("r", 2.5)), 99)
		"veil":
			var radius := float(extra.get("r", 6.0))
			FX.spawn(VFXLib.particles(Color(0.35, 0.33, 0.38, 0.75), 70, 2.2, true, 1.6, 2.5, 180.0, Vector3(0, 0.4, 0), radius * 0.5, false), at + Vector3.UP * 0.6)
			FX.spawn(VFXLib.ring_wave(Color(0.5, 0.4, 0.65, 0.7), radius, 0.5), at)

func share_telegraph(pos: Vector3, radius: float, delay: float, color: Color, shape: String, inner: float, source: Node) -> void:
	if not is_active() or not owns_source(source):
		return
	_remote_telegraph.rpc(String(Game.current_map_id), pos, radius, delay, color, shape, inner)

@rpc("any_peer", "unreliable")
func _remote_telegraph(map: String, pos: Vector3, radius: float, delay: float, color: Color, shape: String, inner: float) -> void:
	if map != String(Game.current_map_id) or FX.world == null or Game.travelling:
		return
	AreaEffects.delayed(FX.world, pos, radius, delay, null, null, 0, color, shape, inner)

# ---- Chat ---------------------------------------------------------------------------------------------------------

func send_chat(text: String) -> void:
	if not is_active():
		return
	var h := Game.hero
	_chat.rpc(h.hero_name if h else "Hero", text)

@rpc("any_peer", "reliable")
func _chat(who: String, text: String) -> void:
	if Game.ui_root and is_instance_valid(Game.ui_root):
		var col := player_color(multiplayer.get_remote_sender_id())
		Game.ui_root.chat.add_line("◆ %s: %s" % [who, text.substr(0, 160)], col.lightened(0.2))

func _chat_system(text: String) -> void:
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.chat.add_line(text, UITheme.GOLD)
	if is_host():
		_chat_sys_remote.rpc(text)

@rpc("authority", "reliable")
func _chat_sys_remote(text: String) -> void:
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.chat.add_line(text, UITheme.GOLD)
