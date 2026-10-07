extends Node
## Multiplayer (autoload `Net`). Up to twelve heroes over ENet on PC and Android.
##
##   Host      the party leader opens a room and assigns one combat owner per occupied map.
##   Join      a hero joins at the leader's side once, then uses doors and waypoints independently.
##   Combat    each map keeps its first explorer as owner; every other hero there shares its monsters, even when
##             the leader is elsewhere. Hits and kills route to that owner. Nearby heroes roll personal class loot.
##   Handoff   when the owner leaves, a remaining member restores the map's live monsters and cleared camps from
##             the latest checkpoint. Packets carry a map and generation so old combat cannot leak into a new map.
##   Portal    members cast Team Portal to the leader; the leader picks a member. Movement/damage interrupts the
##             cast. Summon Party remains an optional Go/Stay invitation. No move forces another player to follow.
##   Presence  every player's hero snapshot reaches every other machine wherever they are: the party frames show HP,
##             level and map for all, the minimap shows allies on the same map (arrows; on the rim with the distance
##             when out of sight) and the world map shows where everyone is (bh-015).
##   Revive    a fallen hero can be stood up again by a friend: stand beside them and press Interact (bh-011).
##   Ping      G (or the touch Ping button) marks a spot every player sees for a few seconds (bh-011).
##   Trade     (bh-016) click an ally (or use the party frames / Multiplayer window) and send a Trade Request; if they
##             accept, both put items from their bags and gold on the table, each accepts the same two offers, and each
##             machine swaps on its own hero (TradeRules). Any change to either offer clears both acceptances.
##   Chat      the chat box is shared; joins and leaves also show as notices.
## Everything else (inventory, shops, crafting, dialogue, saving) stays per player, on their own machine.

signal state_changed
signal peers_changed
signal chat_received(peer: int, text: String)
## A player's profile changed (level, map, class advancement ...) on this machine's copy of the roster. Unlike
## peers_changed it does not resend appearances; name plates listen to it (Class Transcendence).
signal roster_updated
signal lan_games_changed
signal trade_changed                 # the trade window's state moved: opened, an offer changed, accepted, closed

const PROTOCOL := 23                 # 23 (bh-042): the Abyss (level-90+ rules, bullet patterns, Curse of Stillness and Armour Rip shared as FX, the Abyss dungeons and bosses); 22 (bh-041): trades confirm through the server without stalling, Eschaton rarity, Tempo commands; 15: official accounts, dedicated coordinator and separate custom rooms; 16 (bh-030): profile pictures; 17 (bh-033): arena events; 18 (bh-034): Ascendant rarities; 20: Class Transcendence (profile "path", ally support, new skill effects); 21 (bh-040): the Descent (combat and experience rules past level 80)
                                     # 19 (bh-035): hero snapshots relayed by the room host per map and distance, light checkpoints, idle monsters not re-sent
                                     # 4 (bh-015): independent exploring, party summons; 5 (bh-016): player trades;
                                     # 6 (bh-018): socketed items and crystals; 7: separate belt capacity and stat rules
                                     # 8: item-level combat growth; 9: per-map combat owners, checkpoints and Team Portal
                                     # 10 (bh-023): heroes share one body, their looks and all worn gear travel
                                     # 11 (bh-024): the Leggings slot and its items
                                     # 12: roster-identified chat, mentions and host-only cheats
                                     # 13 (bh-027): guilds in profiles, banners, guild invites, whispers, Showcase
const SUMMON_WAIT := 30.0            # seconds a summoned player has to answer before it counts as Stay
const SUMMON_COOLDOWN := 8.0
const BESIDE_M := 20.0               # a player this close to the host on the same map is not summoned
const PORT := 24680
const DISCOVERY_PORT := 24681
const MAX_PLAYERS := 12
const MAX_CLIENTS := MAX_PLAYERS - 1 # Custom host occupies one player slot; a dedicated server occupies none.
const ALLY_RATE := 15.0
const ENEMY_RATE := 12.0
const ENEMY_BATCH := 20             # monsters per unreliable state packet (about 50 bytes each packed: stays under the MTU)
const ENEMY_RANGE := 70.0            # monsters farther than this from a client's hero are not streamed to it
## bh-035 interest management (MMO-style): a 6-hero map cost its owner 3.5 Mbit/s upstream and every member 0.9 Mbit/s
## down, mostly snapshots nobody needed. A monster that has not moved or changed is re-sent only as a keep-alive; one far
## from a hero streams at a third of the rate. Hero snapshots go to the room host, which forwards them at full rate only
## to heroes close by on the same map and as a slim presence update to everyone else.
const ENEMY_KEEPALIVE := 1.0         # seconds: an unchanged monster is still re-sent this often (replicas expire after GONE_AFTER)
const ENEMY_FAR := 35.0              # metres: monsters farther than this from a hero go out at ENEMY_RATE / ENEMY_FAR_EVERY,
const ENEMY_FAR_EVERY := 3           # and so do calm ones (patrolling, not fighting): replicas dead-reckon in between
const ALLY_NEAR := 80.0              # metres: allies farther than this on the same map arrive at ALLY_RATE / ALLY_FAR_EVERY
const ALLY_FAR_EVERY := 3
const ALLY_AWAY_EVERY := 8           # heroes on another map get a slim presence snapshot (HP, map, place) at ALLY_RATE / 8
const CHECKPOINT_HOST_EVERY := 2     # the room host gets the full checkpoint every 2 s (the camps part each second it changes),
const CHECKPOINT_MEMBER_EVERY := 6   # members on the map every 6 s
const APPEARANCE_EVERY := 150        # full appearance every N ally snapshots (10 s), whenever gear changes and when the roster changes
const GONE_AFTER := 4.0
const CONNECT_TIMEOUT := 10.0        # seconds a join may take before it is given up with a clear message
const REVIVE_HP := 0.4               # a friend's revive stands you up with this share of your HP
const PING_LIFE := 5.0
const RECENT_PATH := "user://net_recent.cfg"

enum Mode { OFFLINE, HOST, CLIENT }

var mode := Mode.OFFLINE
var connecting := false
var peers := {}                      # peer id -> {name, cls, level, map}
var lan_games := {}                  # "ip" -> {name, host, map, players, port, t}
var last_error := ""
var protocol_override := -1          # probes only: pretend to be another game version
var following := false               # a client is loading the host's map: its own travel rules are lifted

var _peer: ENetMultiplayerPeer
var dedicated := false
var official_room := false
var room_name := "Friends' Game"
var host_port := PORT
var _server_config := {}
var _server_leases := {}
var _introductions := {}
var _heartbeat_t := 0.0
var _stats_t := 30.0
var _server_healthy := true
var _directory_secret := ""
var _directory_t := 0.0
var _directory_busy := false
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
var _appearance_cache := {}
var _appearance_rev := {}            # "peer:key" -> times its appearance arrived (avatars re-dress only when it moves)
var _app_sig := {}                   # local ally key -> appearance hash (resend on change)
var _relay_n := {}                   # room host: "from>to" -> snapshots seen, for the reduced far / other-map rates
var _enemy_tick := 0                 # world authority: snapshot rounds sent (far monsters go out every ENEMY_FAR_EVERY)
var _enemy_last := {}                # world authority: eid -> the state last streamed (to spot idle monsters)
var _enemy_sent := {}                # world authority: peer -> {eid: [msec, the _enemy_last entry that peer was last sent]}
var _checkpoint_n := 0
var _kill_checkpoint := false        # a monster died since the last checkpoint
var _kill_checkpoint_t := 0.0
var _light_sig := 0                  # hash of the camps / cleared / arena part members last received
var _unloading := false              # the old map is leaving the tree: its monsters are not "gone", the map is
var _connect_t := 0.0
var _joining_addr := ""
var _travel_pending := {}            # host: the request being asked about {from, req}
var _travel_asked_t := -99.0         # client: when this machine last asked (one request at a time)
var last_room := ""                  # the last room code / address this machine joined (Multiplayer > Rejoin)
var status := {}                     # peer id -> {map, pos, yaw, hp, mhp, alive, lvl, t}: every player, wherever they are
var _worlds := {}                    # map -> {owner, epoch, state}; assigned by the room host
var _world_serial := 0
var _world_owner := 0
var _world_epoch := 0
var _checkpoint_t := 0.0
var _host_shared := false            # another member owns this map; local enemies are replicas
var _share_t := 0.0
var _arrived := false                # client: has reached the host once after joining (later host moves do not drag it)
var _summon := {}                    # client: the summons being asked about {map, t}
var _summon_t := -99.0               # host: when the party was last summoned
## The trade in progress ({} = none): {peer, name, phase ("asking" | "open"), mine {gold, items}, theirs {gold, items},
## rev, their_rev, my_ok, their_ok, committing, their_ready, sent (wire form of the offer last sent)}.
var trade := {}
var _trade_asked_t := -99.0
var _trade_incoming := {}            # a request being asked about: {peer, name, t}

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)
	get_tree().node_added.connect(_on_node_added)
	Events.actor_died.connect(_on_actor_died)
	Events.stage_cleared.connect(_on_stage_cleared)
	Game.session_ended.connect(func() -> void:
		if is_active():
			leave(false))
	Events.player_leveled.connect(func(_l: int, _g: int) -> void: update_profile())
	Events.guild_customised.connect(_on_my_guild_changed)
	Events.guild_changed.connect(_on_my_guild_changed)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _on_my_guild_changed())
	peers_changed.connect(_on_peers_for_guilds)
	# someone joined, left or changed maps: send our looks again with the next snapshot, so newcomers see us at once
	peers_changed.connect(func() -> void: _app_sig.clear())
	var cfg := ConfigFile.new()
	if cfg.load(RECENT_PATH) == OK:
		last_room = String(cfg.get_value("net", "last_room", ""))

# ---- State --------------------------------------------------------------------------------------------------------

func is_active() -> bool:
	return mode != Mode.OFFLINE

func is_host() -> bool:
	return mode == Mode.HOST

func is_client() -> bool:
	return mode == Mode.CLIENT

func my_id() -> int:
	return multiplayer.get_unique_id() if is_active() and _peer and _peer.get_connection_status() != MultiplayerPeer.CONNECTION_DISCONNECTED else 1

## Each human player's colour: their name plate, foot ring, chat name and party entry (bh-008).
const PLAYER_COLORS := [Color(1.0, 0.78, 0.3), Color(0.35, 0.8, 1.0), Color(0.55, 1.0, 0.45), Color(1.0, 0.45, 0.75)]

func player_color(peer: int) -> Color:
	var ids := peers.keys()
	ids.sort()
	var i := ids.find(peer)
	return PLAYER_COLORS[(i if i >= 0 else absi(peer)) % PLAYER_COLORS.size()]

func player_count() -> int:
	return peers.size()

var _traffic_msec := 0

## Bytes this machine's ENet host has sent and received since the previous call: {"sent", "received", "seconds"}.
## The dedicated coordinator logs it every 30 seconds; the performance probes read it to measure bandwidth per player count.
func pop_traffic() -> Dictionary:
	var now := Time.get_ticks_msec()
	var seconds := maxf(0.001, (now - (_traffic_msec if _traffic_msec > 0 else now - 30000)) * 0.001)
	_traffic_msec = now
	var host: ENetConnection = _peer.get_host() if _peer else null
	if host == null:
		return {"sent": 0.0, "received": 0.0, "seconds": seconds}
	return {"sent": host.pop_statistic(ENetConnection.HOST_TOTAL_SENT_DATA), "received": host.pop_statistic(ENetConnection.HOST_TOTAL_RECEIVED_DATA), "seconds": seconds}

func _profile() -> Dictionary:
	var h: HeroData = Game.hero
	return {"name": h.hero_name if h else "Hero", "cls": String(h.cls.id) if h else "knight", "path": profile_path(h),
		"level": h.progress.level if h else 1, "map": String(Game.current_map_id),
		"dungeon_level": int(h.world_flags.get(DungeonGrowth.visit_key(DataDungeons.parse(h.current_map)[0]), h.progress.level)) if h else 1,
		"device": "Mobile" if Settings.is_mobile_device() else "PC", "guild": guild_profile(h),
		"scope": SaveSystem.scope, "room": SaveSystem.custom_room}

## Class Transcendence: the advancement this hero shows other players. An official character shows only what the server
## has confirmed (the last acknowledged save), never an advancement still waiting for its save.
static func profile_path(h: HeroData) -> String:
	if h == null:
		return ""
	if Official.active:
		var saved: Variant = Official._confirmed_save.get("hero", {}).get("transcendence", {}) if Official._confirmed_save.get("hero", {}) is Dictionary else {}
		var lvl := int(Official._confirmed_save.get("hero", {}).get("progress", {}).get("level", h.progress.level)) if Official._confirmed_save.get("hero", {}) is Dictionary else h.progress.level
		var res := ClassTranscendence.from_save(h.cls.id, lvl, saved)
		return ",".join((res.path as Array).map(func(x): return String(x)))
	return ClassTranscendence.path_text(h)

## A player's current class id (Grand Paladin, Hunter ...) from the roster: their family and their advancement, checked
## against each other and their level. Never free text from the peer.
func peer_class_id(peer: int) -> StringName:
	var info: Dictionary = peers.get(peer, {})
	var fam := StringName(String(info.get("cls", "knight")))
	if not DataTranscendence.is_family(fam):
		return &""
	return ClassTranscendence.peer_class_id(fam, int(info.get("level", 1)), info.get("path", ""))

func peer_class_name(peer: int) -> String:
	return ClassTranscendence.class_name_of(peer_class_id(peer))

## Dedicated coordinator has no playable hero and does not consume one of the twelve slots.
func host_dedicated(config: Dictionary) -> String:
	_server_config = config
	var result := {}
	for attempt in 5:
		result = await _server_request("/internal/start")
		if not result.has("error"):
			break
		await get_tree().create_timer(1.0).timeout
	if result.has("error"):
		return "Account service unavailable: " + String(result.error)
	_peer = ENetMultiplayerPeer.new()
	var error := _peer.create_server(int(config.get("game_port", PORT)), MAX_PLAYERS)
	if error != OK:
		return "Could not open the official game port (error %d)." % error
	multiplayer.multiplayer_peer = _peer
	mode = Mode.HOST
	dedicated = true
	official_room = true
	peers = {}
	print("Official Beyond Heroes game server listening; maximum 12 players.")
	return ""

func _server_request(path: String, body := {}) -> Dictionary:
	var http := HTTPRequest.new()
	http.timeout = 5.0
	http.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(http)
	var ca := X509Certificate.new()
	if ca.load(String(_server_config.get("certificate", ""))) != OK:
		http.queue_free()
		return {"error": "Server certificate missing."}
	http.set_tls_options(TLSOptions.client(ca))
	var error := http.request("https://127.0.0.1:%d%s" % [int(_server_config.get("api_port", 8443)), path],
		PackedStringArray(["Content-Type: application/json", "X-Server-Key: " + String(_server_config.get("server_key", ""))]), HTTPClient.METHOD_POST, JSON.stringify(body))
	if error != OK:
		http.queue_free()
		return {"error": "Could not start account service connection."}
	var reply: Array = await http.request_completed
	http.queue_free()
	if int(reply[0]) != HTTPRequest.RESULT_SUCCESS:
		return {"error": "Account service connection failed (HTTP result %d)." % int(reply[0])}
	var parsed = JSON.parse_string((reply[3] as PackedByteArray).get_string_from_utf8())
	return parsed if parsed is Dictionary else {"error": "Account service response unreadable."}

func _server_heartbeat() -> void:
	var result := await _server_request("/internal/heartbeat")
	_server_healthy = not result.has("error")
	if not _server_healthy:
		for id in _server_leases.keys():
			_reject_peer(int(id), "The official account service stopped. Gameplay is paused; reconnect when it returns.")
		return
	var valid: Array = result.get("leases", [])
	for id in _server_leases.keys():
		if not valid.has(_server_leases[id]):
			_reject_peer(int(id), "Your official play session expired. Load your last server save to reconnect.")

func _publish_custom() -> void:
	if _directory_busy or dedicated or SaveSystem.scope != "custom":
		return
	_directory_busy = true
	var result := await Official.request("/custom/register" if _directory_secret == "" else "/custom/heartbeat", {
		"room": SaveSystem.custom_room, "name": room_name, "port": host_port, "players": player_count(), "secret": _directory_secret}, HTTPClient.METHOD_POST, false)
	_directory_busy = false
	if result.has("error"):
		_directory_secret = ""
	else:
		_directory_secret = String(result.get("secret", _directory_secret))

# ---- Host / join / leave ------------------------------------------------------------------------------------------

## Open this running game to others. Returns "" or an error to show.
func host_game(port := PORT) -> String:
	if Official.active:
		return "Official characters cannot host custom games. Choose Custom Games from the main menu."
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
	host_port = port
	peers = {1: _profile()}
	_known.clear()
	_enemy_sent.clear()
	_enemy_last.clear()
	_host_enemies.clear()
	_next_eid = 1
	_reassign_worlds()
	_start_broadcast()
	Events.notify.emit("Your world is open. Others can join from Multiplayer > Join.", &"info")
	_chat_system("%s opened the world to other heroes." % peers[1].name)
	state_changed.emit()
	peers_changed.emit()
	_publish_custom()
	return ""

## Join a hosted game at `address` (a room code, an IP or a host name). Returns "" or an error; the result arrives later.
func join_game(address: String, port := PORT) -> String:
	if is_active():
		return "Already connected."
	if not Game.in_session:
		return "Start or continue a game first, then join."
	address = address.strip_edges()
	var typed := address
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
	official_room = Official.active
	connecting = true
	_connect_t = 0.0
	_joining_addr = typed
	last_error = ""
	state_changed.emit()
	return ""

## Leave the party. Restore shared combat locally at its latest checkpoint, keeping this map and its loot.
func leave(reload := true) -> void:
	if _directory_secret != "":
		Official.request("/custom/remove", {"room": SaveSystem.custom_room, "secret": _directory_secret}, HTTPClient.METHOD_POST, false)
		_directory_secret = ""
	var was_shared := _host_shared
	var state: Dictionary = _worlds.get(String(Game.current_map_id), {}).get("state", {}).duplicate(true)
	if is_active() and not is_host():
		_send_checkpoint()
	if is_active() and _peer:
		if is_host():
			_chat_system("The host closed the world.")
		_peer.close()
	multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	_peer = null
	mode = Mode.OFFLINE
	official_room = false
	connecting = false
	following = false
	peers.clear()
	status.clear()
	_known.clear()
	_enemy_sent.clear()
	_enemy_last.clear()
	_host_enemies.clear()
	_host_shared = false
	_worlds.clear()
	_world_owner = 0
	_world_epoch = 0
	_portal_pending = {}
	_portal_serial += 1
	_portal_ready_at = 0.0
	_arrived = false
	_summon = {}
	_trade_incoming = {}
	trade_reset()
	_banner_sent.clear()
	_pic_sent.clear()
	profile_pictures.clear()
	_sync_sent.clear()
	_guild_asked = {}
	_stop_broadcast()
	_clear_avatars()
	_appearance_cache.clear()
	_clear_replicas()
	state_changed.emit()
	peers_changed.emit()
	if reload and Game.in_session and was_shared and Game.current_map:
		_drop_local_monsters(Game.current_map)
		if not state.is_empty():
			NetWorld.restore(state)
		else:
			Spawner.populate(Game.current_map, Game.difficulty)

func _on_peer_connected(_id: int) -> void:
	if dedicated:
		_introductions[_id] = Time.get_ticks_msec()

func _on_peer_disconnected(id: int) -> void:
	if not is_active():
		return
	var who: String = peers.get(id, {}).get("name", "A hero")
	_introductions.erase(id)
	NetGuard.forget(id)
	if dedicated and _server_leases.has(id):
		_server_request("/internal/disconnect", {"lease": _server_leases[id]})
		_server_leases.erase(id)
	peers.erase(id)
	status.erase(id)
	_known.erase(id)
	_enemy_sent.erase(id)
	_remove_avatars_of(id)
	for key in _appearance_cache.keys():
		if key.begins_with("%d:" % id):
			_appearance_cache.erase(key)
	if int(trade.get("peer", -1)) == id:
		trade_reset("%s left the game. The trade was cancelled." % who)
	if int(_trade_incoming.get("peer", -1)) == id:
		_trade_incoming = {}
	_banner_sent.erase(id)
	_pic_sent.erase(id)
	profile_pictures.erase(id)
	_sync_sent.erase(id)
	if is_host():
		_chat_system("%s left." % who, true)
		_reassign_worlds()
		_rpc_peers()
	if _travel_pending.get("from", 0) == id:
		_travel_pending = {}
	peers_changed.emit()

func _on_connected() -> void:
	_remember_room(_joining_addr)
	var profile := _profile()
	if Official.active:
		profile["ticket"] = Official.ticket
	_hello.rpc_id(1, protocol_override if protocol_override >= 0 else PROTOCOL, profile)

## Remember the room a join reached, for Multiplayer > Rejoin (never a probe's loopback address).
func _remember_room(addr: String) -> void:
	if addr == "" or addr.begins_with("127.") or addr == NetCodec.room_code("127.0.0.1", PORT, PORT):
		return
	last_room = addr
	var cfg := ConfigFile.new()
	cfg.set_value("net", "last_room", addr)
	cfg.save(RECENT_PATH)

## Why joining did not work, for the player. Signing in already succeeded for an official server, so the game port is the likely
## problem there; for a custom game it is the room code or the host's network.
func _join_failure_text(waited_out: bool) -> String:
	if Official.active:
		return "Signed in, but the game connection to %s could not be made%s. The server may have just restarted, or this network may block UDP port %d. Try again, or try another network (for example mobile data)." % [
			Official.url.trim_prefix("https://").get_slice(":", 0), " in time" if waited_out else "", PORT]
	if waited_out:
		return "No answer from %s. Check the room code, that the host pressed Host Game, and that you are on the same network (or the same VPN)." % _joining_addr
	return "Could not connect to the host. Check the room code and that the host pressed Host Game."

func _on_connection_failed() -> void:
	last_error = _join_failure_text(false)
	Events.notify.emit(last_error, &"error")
	if Official.active:
		Official.game_disconnected(last_error)
	leave(false)

func _on_server_disconnected() -> void:
	if Official.active:
		Official.game_disconnected("The official game server disconnected. Your confirmed saves remain on the server.")
		leave(false)
		return
	Events.notify.emit("The host closed the world. You are playing alone again.", &"info")
	leave(true)

@rpc("any_peer", "reliable")
func _hello(proto: int, profile: Dictionary) -> void:
	if not is_host():
		return
	var id := multiplayer.get_remote_sender_id()
	if peers.has(id) or (dedicated and _introductions.get(id, -1) < 0):
		return
	if not NetGuard.allow(id, "hello", 0.5, 2.0):
		return
	if proto != PROTOCOL:
		_rejected.rpc_id(id, version_refusal(PROTOCOL, proto))
		get_tree().create_timer(0.5).timeout.connect(func() -> void:
			if _peer:
				_peer.disconnect_peer(id))
		return
	profile = NetGuard.clean_profile(profile)
	if profile.is_empty():
		_reject_peer(id, "The game could not read your player information. Update the game and try again.")
		return
	if dedicated:
		_introductions[id] = -1 # One redemption per peer, even if it sends overlapping introductions.
		var result := await _server_request("/internal/redeem", {"ticket": profile.get("ticket", ""), "peer": id})
		if not _peer or not multiplayer.get_peers().has(id):
			if not result.has("error"):
				_server_request("/internal/disconnect", {"lease": result.get("lease", "")})
			return
		if result.has("error") or not _server_healthy:
			_reject_peer(id, String(result.get("error", "Official account service unavailable.")))
			return
		var character: Dictionary = result.get("character", {})
		profile["name"] = character.get("name", "Hero")
		profile["cls"] = character.get("class", "knight")
		profile["level"] = character.get("level", 1)
		profile["path"] = String(character.get("path", ""))       # the server's stored advancement, never the client's claim
		profile["userid"] = result.get("userid", "")
		profile["character"] = character.get("id", "")
		_server_leases[id] = result.get("lease", "")
		_introductions.erase(id)
	elif SaveSystem.scope == "custom" and (profile.get("scope", "") != "custom" or profile.get("room", "") != SaveSystem.custom_room):
		_reject_peer(id, "This custom game needs a character created for its room. Join it from the main menu server list.")
		return
	profile.erase("ticket")
	profile["name"] = String(profile.get("name", "Hero")).left(18)
	profile["level"] = clampi(int(profile.get("level", 1)), 1, BH.LEVEL_CAP)
	profile["map"] = "" # the joining hero has not arrived yet
	peers[id] = profile
	_known[id] = {}
	_enemy_sent[id] = {}
	var p := Game.player as Node3D
	_welcome.rpc_id(id, {"official": dedicated, "map": String(Game.current_map_id), "pos": p.global_position if p else Vector3.ZERO,
		"yaw": p.rotation.y if p else 0.0, "peers": peers, "worlds": _worlds})
	_chat_system("%s joined (%s)." % [profile.get("name", "A hero"), profile.get("device", "PC")], true)
	_rpc_peers()
	peers_changed.emit()

## What a player is told when their game and the one they are joining speak different online versions.
static func version_refusal(host_version: int, your_version: int) -> String:
	if your_version < host_version:
		return "Your game is older than this one (online version %d, yours is %d). Update your game, then try again." % [host_version, your_version]
	return "This game is older than yours (online version %d, yours is %d). Ask the host or server owner to update, or play offline meanwhile." % [host_version, your_version]

func _reject_peer(id: int, reason: String) -> void:
	if _peer and multiplayer.get_peers().has(id):
		_rejected.rpc_id(id, reason)
		get_tree().create_timer(0.5).timeout.connect(func() -> void:
			if _peer:
				_peer.disconnect_peer(id))

@rpc("authority", "reliable")
func _rejected(why: String) -> void:
	last_error = why
	Events.notify.emit(why, &"error")
	if Official.active:
		Official.game_disconnected(why)
	leave(false)

@rpc("authority", "reliable")
func _welcome(info: Dictionary) -> void:
	if bool(info.get("official", false)) != Official.active:
		_rejected("Official characters cannot enter custom games. Choose the matching server from the main menu.")
		return
	connecting = false
	official_room = bool(info.get("official", false))
	peers = info.get("peers", {})
	_worlds = info.get("worlds", {})
	Events.notify.emit("Joined Official Beyond Heroes." if official_room else "Joined %s's world." % peers.get(1, {}).get("name", "the host"), &"info")
	state_changed.emit()
	peers_changed.emit()
	if official_room:
		_arrived = true
		on_local_map_loaded(Game.current_map_id)
		Official.game_connected()
		Game.ui_blocking = false
		get_tree().paused = false
	else:
		_follow(StringName(info.map), info.pos, float(info.yaw))

func _rpc_peers() -> void:
	for id in _live_peers():
		# bh-035: a map's saved combat state goes only to that map's owner (who restores from it); every roster change used
		# to send every map's full monster list to every player, a burst of up to a megabyte with twelve on six maps
		var worlds := {}
		for map in _worlds:
			var entry: Dictionary = _worlds[map]
			if int(entry.get("owner", 0)) == int(id):
				worlds[map] = entry
			else:
				var lean := entry.duplicate()
				lean.erase("state")
				worlds[map] = lean
		_peers_update.rpc_id(id, peers, worlds)

## Peers this machine can still send to. ENet empties a lost client's channels a few frames before the engine reports
## the disconnect, so a broadcast made while handling one departure logs "max channels: 0" for every other client
## that left in the same frame (twelve probe clients quitting together produced dozens of these).
func _live_peers() -> Array:
	var out := []
	if _peer == null:
		return out
	for id in multiplayer.get_peers():
		var link := _peer.get_peer(id)
		if link == null or link.get_state() == ENetPacketPeer.STATE_CONNECTED:
			out.append(id)
	return out

@rpc("authority", "reliable")
func _peers_update(p: Dictionary, worlds: Dictionary) -> void:
	peers = p
	for map in worlds:
		if int(_worlds.get(map, {}).get("epoch", -1)) == int(worlds[map].get("epoch", 0)) and _worlds[map].get("rewarded", false):
			worlds[map]["rewarded"] = true
		if not worlds[map].has("state"):        # not this machine's map to restore: keep the copy its checkpoints left
			worlds[map]["state"] = _worlds.get(map, {}).get("state", {})
	_worlds = worlds
	_check_shared()
	peers_changed.emit()
	roster_updated.emit()

# ---- Following the host between maps ------------------------------------------------------------------------------

## Game.load_map calls these around every map swap on this machine.
func map_unloading() -> void:
	_send_checkpoint()
	_unloading = true
	_world_owner = 0
	_world_epoch = 0
	_host_enemies.clear()

func on_local_map_loaded(id: StringName) -> void:
	_unloading = false
	if not is_active():
		return
	_clear_avatars()
	_clear_replicas()
	_app_sig.clear()
	_known.clear()
	_enemy_sent.clear()
	_enemy_last.clear()
	if peers.has(my_id()):
		peers[my_id()]["map"] = String(id)
	update_profile()
	if is_host():
		_reassign_worlds()
		_rpc_peers()
	else:
		_in_map.rpc_id(1, String(id))
	_check_shared()

## Compatibility name for map loaders: true whenever another member runs this map's combat.
func host_on(id: StringName) -> bool:
	var owner := world_owner(id)
	return is_active() and owner != 0 and owner != my_id()

func world_owner(id: StringName) -> int:
	return int(_worlds.get(String(id), {}).get("owner", 0))

func is_world_authority() -> bool:
	return is_active() and _peer != null and _peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED and not _unloading and world_owner(Game.current_map_id) == my_id()

static func choose_world_owner(members: Dictionary, map: String, previous: int) -> int:
	if members.has(previous) and String(members[previous].get("map", "")) == map:
		return previous
	var ids := members.keys()
	ids.sort()
	for id in ids:
		if String(members[id].get("map", "")) == map:
			return int(id)
	return 0

## Keep the first member on a map in charge, even when the party leader arrives later.
func _reassign_worlds() -> void:
	if not is_host():
		return
	var maps := _worlds.keys()
	for profile in peers.values():
		var map := String(profile.get("map", ""))
		if map != "" and not maps.has(map):
			maps.append(map)
	for map in maps:
		var old: Dictionary = _worlds.get(map, {})
		var owner := choose_world_owner(peers, map, int(old.get("owner", 0)))
		if owner == 0:
			_worlds.erase(map) # an empty map starts a new visit next time
		elif owner != int(old.get("owner", 0)):
			_world_serial += 1
			_worlds[map] = {"owner": owner, "epoch": _world_serial, "state": old.get("state", {})}
	_check_shared()

func _follow(map: StringName, pos: Vector3, yaw: float) -> void:
	if following or Game.travelling:
		return
	following = true
	await Game.net_follow(map, pos, yaw)
	following = false
	_arrived = true
	if is_active():
		_check_shared()

func _check_shared() -> void:
	if not is_active() or not Game.in_session or Game.current_map == null or _unloading:
		return
	var entry: Dictionary = _worlds.get(String(Game.current_map_id), {})
	var owner := int(entry.get("owner", 0))
	var epoch := int(entry.get("epoch", 0))
	if owner == 0 or (_world_owner == owner and _world_epoch == epoch):
		return
	var was_remote := _host_shared
	_world_owner = owner
	_world_epoch = epoch
	_host_shared = owner != my_id()
	_clear_replicas()
	_host_enemies.clear()
	_known.clear()
	_enemy_sent.clear()
	_enemy_last.clear()
	if _host_shared:
		_drop_local_monsters(Game.current_map)
	else:
		var state: Dictionary = entry.get("state", {})
		if not state.is_empty():
			_drop_local_monsters(Game.current_map)
			NetWorld.restore(state)
		elif Spawner.current() == null:
			Spawner.populate(Game.current_map, Game.difficulty)
		_register_existing_enemies()
		_send_checkpoint()
	if was_remote != _host_shared:
		Events.notify.emit("Party combat synchronized. You can keep exploring independently.", &"info")

## The map's combat state (every live monster, cleared camps, arena) for a hand-off. The room host keeps the latest copy
## every second; members on the map hold one too (their own restore when they leave the party) but get the full copy only
## when `full` (every CHECKPOINT_MEMBER_EVERY seconds) and otherwise just the small camps / arena part, when it changed
## (bh-035: the full copy to every member every second was most of the map owner's upload).
func _send_checkpoint(full := true, host_full := true) -> void:
	if not is_world_authority() or Game.current_map == null:
		return
	var state := NetWorld.capture(_host_enemies)
	var map := String(Game.current_map_id)
	if is_host():
		_worlds[map]["state"] = state
	var light := {}
	for k in state:
		if k != "enemies":
			light[k] = state[k]
	var sig := hash(light)
	var light_due := sig != _light_sig
	if full or light_due:
		_light_sig = sig
	var targets := peers.keys()
	if not is_host() and not peers.has(1):
		targets.append(1)       # the dedicated coordinator is not on the roster but must hold the latest state for a hand-off
	for pid in targets:
		if int(pid) == my_id():
			continue
		if (int(pid) == 1 and (host_full or full)) or (full and _peer_map(pid) == map):
			_world_checkpoint.rpc_id(pid, map, _world_epoch, state)
		elif light_due and (int(pid) == 1 or _peer_map(pid) == map):
			_world_checkpoint.rpc_id(pid, map, _world_epoch, light)

@rpc("any_peer", "reliable")
func _world_checkpoint(map: String, epoch: int, state: Dictionary) -> void:
	var entry: Dictionary = _worlds.get(map, {})
	if int(entry.get("owner", 0)) != multiplayer.get_remote_sender_id() or int(entry.get("epoch", -1)) != epoch:
		return
	if not NetGuard.fits(state, NetGuard.MAX_CHECKPOINT_BYTES):
		return
	if not state.has("enemies"):
		# a light checkpoint (bh-035): camps, cleared camps and arena moved on; the monster list stays the last full one
		var merged: Dictionary = (entry.get("state", {}) as Dictionary).duplicate()
		merged.merge(state, true)
		state = merged
	if state.has("enemies"):              # no full copy yet: nothing a restore could use
		entry["state"] = state
	if _world_sender(map, epoch) and Game.current_map:
		var sp := Spawner.current()
		if sp == null:
			sp = Spawner.new()
			sp.name = "Spawner"
			sp.map = Game.current_map
			Game.current_map.add_child(sp)
		sp.camps.clear()
		for camp in state.get("camps", []):
			sp.camps[camp] = []
		sp.cleared_camps = state.get("cleared", {}).duplicate()
		if sp.cleared_camps.has(DataDungeons.SEAL_ZONE):
			Events.camp_cleared.emit(StringName(map), DataDungeons.SEAL_ZONE, 0, sp.camps.size())
		sp.stage_done = bool(state.get("done", false))
		if state.get("arena", {}) is Dictionary:
			ArenaState.apply(Game.current_map, state.get("arena", {}))
		sp.minibosses.clear()
		for e: Enemy in _replicas.values():
			if is_instance_valid(e) and e.is_miniboss():
				sp.minibosses.append(e)

func _on_stage_cleared(map: StringName) -> void:
	if not is_world_authority():
		return
	for pid in peers:
		if pid != my_id() and _peer_map(pid) == String(map):
			_stage_complete.rpc_id(pid, String(map), _world_epoch)
	_send_checkpoint.call_deferred()

@rpc("any_peer", "reliable")
func _stage_complete(map: String, epoch: int) -> void:
	if not _world_sender(map, epoch) or Game.hero == null:
		return
	var entry: Dictionary = _worlds.get(map, {})
	if entry.get("rewarded", false):
		return
	entry["rewarded"] = true
	Game.hero.stages_cleared[StringName(map)] = int(Game.hero.stages_cleared.get(StringName(map), 0)) + 1
	Game.hero.add_clear()
	Events.stage_cleared.emit(StringName(map))

func _world_sender(map: String, epoch: int) -> bool:
	return is_active() and not _unloading and map == String(Game.current_map_id) and epoch == _world_epoch \
		and _world_owner != my_id() and multiplayer.get_remote_sender_id() == _world_owner

func _drop_local_monsters(map: Node) -> void:
	for n in [map.get_node_or_null(^"Spawner"), map.get_node_or_null(^"CombatDirector")]:
		if n:
			map.remove_child(n)
			n.queue_free()
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and not (e as Enemy).net_replica and map.is_ancestor_of(e):
			e.queue_free()

@rpc("any_peer", "reliable")
func _in_map(map: String) -> void:
	if not is_host() or DB.map_def(StringName(map)) == null:
		return
	var id := multiplayer.get_remote_sender_id()
	if not peers.has(id) or not NetGuard.allow(id, "map", 3.0, 8.0):
		return
	peers[id]["map"] = map
	_known[id] = {}
	_enemy_sent[id] = {}
	_reassign_worlds()
	_rpc_peers()

## May this machine take a door, a waypoint or a portal right now? Always (bh-015: everyone explores on their own;
## until bh-014 a client had to ask the host to lead the party).
func may_travel() -> bool:
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
		"max": MAX_CLIENTS + 1, "port": host_port}
	msg["room"] = SaveSystem.custom_room if SaveSystem.scope == "custom" else ""
	msg["name"] = room_name
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
	if dedicated:
		_heartbeat_t -= delta
		if _heartbeat_t <= 0.0:
			_heartbeat_t = 10.0
			_server_heartbeat()
		_stats_t -= delta
		if _stats_t <= 0.0:
			var t := pop_traffic()
			_stats_t = 30.0
			print("NET_STATS players=%d sent_kbps=%.1f received_kbps=%.1f over=%.0fs" % [peers.size(), t.sent * 8.0 / 1000.0 / t.seconds, t.received * 8.0 / 1000.0 / t.seconds, t.seconds])
		for id in _introductions.keys():
			var stamp: int = _introductions[id]
			if stamp >= 0 and Time.get_ticks_msec() - stamp > 15000:
				_introductions.erase(id)
				_peer.disconnect_peer(int(id))
		return
	if is_host():
		_directory_t -= delta
		if _directory_t <= 0.0:
			_directory_t = 15.0
			_publish_custom()
	_portal_tick()
	if is_host():
		_bcast_t -= delta
		if _bcast_t <= 0.0:
			_bcast_t = 1.0
			_broadcast()
	if connecting:
		_connect_t += delta
		if _connect_t > CONNECT_TIMEOUT:
			last_error = _join_failure_text(true)
			Events.notify.emit(last_error, &"error")
			if Official.active:
				Official.game_disconnected(last_error)
			leave(false)
		return
	if not Game.in_session or Game.travelling or following:
		return
	_ally_t -= delta
	if _ally_t <= 0.0:
		_ally_t = 1.0 / ALLY_RATE
		_send_allies()
	_check_shared()
	if is_world_authority():
		_checkpoint_t -= delta
		_kill_checkpoint_t -= delta
		if _checkpoint_t <= 0.0:
			_checkpoint_t = 1.0
			_checkpoint_n += 1
			_send_checkpoint(_checkpoint_n % CHECKPOINT_MEMBER_EVERY == 0, _checkpoint_n % CHECKPOINT_HOST_EVERY == 0)
		elif _kill_checkpoint and _kill_checkpoint_t <= 0.0:
			# kills: the room host's copy (and the members' camps) catch up at most twice a second
			_kill_checkpoint = false
			_kill_checkpoint_t = 0.5
			_send_checkpoint(false, true)
		_enemy_t -= delta
		if _enemy_t <= 0.0:
			_enemy_t = 1.0 / ENEMY_RATE
			_send_enemies()
	else:
		_expire_replicas()
		_share_t -= delta
		if _share_t <= 0.0:
			_share_t = 0.25
			_check_shared()

# ---- Allies (heroes and Tempos) -----------------------------------------------------------------------------------

func _local_allies() -> Array:
	var out := []
	if Game.player is Player and is_instance_valid(Game.player):
		out.append(["p", Game.player])
	for t in get_tree().get_nodes_in_group(&"tempo"):
		if t is Tempo and t.data and is_instance_valid(t):
			out.append(["t%d" % t.data.uid, t])
	# bh-028: the Sand Arena's adventurers, on the machine that runs them
	for f in get_tree().get_nodes_in_group(&"arena_fighter"):
		if f is ArenaFighter and f.data and is_instance_valid(f) and not f.is_queued_for_deletion():
			out.append(["a%d" % f.data.uid, f])
	return out

static func actor_state(a: Actor) -> Array:
	var v := a.visual
	var act := v.current_action() if v else &""
	return [a.global_position, a.rotation.y, a.velocity, a.hp, a.max_hp(), a.alive, String(act),
		v.action_serial if v else 0, v.action_rate if v else 1.0, bool(v._action_loop) if v else false, a.in_combat(), a.level]

func _send_allies() -> void:
	_ally_count += 1
	var pack := []
	var appearances := []
	for pair in _local_allies():
		var a: Actor = pair[1]
		var e := {"k": pair[0], "s": actor_state(a), "n": a.display_name}
		if a is Tempo:
			e["n"] = (a as Tempo).data.tempo_name
		if a is GuildFighter:
			e["g"] = (a as GuildFighter).guild_name
		if a is ArenaFighter:
			e["n"] = a.display_name
			e["af"] = true
		# the look rarely changes: hashing the whole appearance 15 times a second per ally was wasted work, 3 times is plenty
		if a.visual and (_ally_count % 5 == 1 or not _app_sig.has(pair[0])):
			var sig := hash(str(a.visual.appearance)) ^ hash(String(a.visual._stance_idle))
			if _ally_count % APPEARANCE_EVERY == 1 or _app_sig.get(pair[0], 0) != sig:
				_app_sig[pair[0]] = sig
				var app := a.visual.appearance.duplicate(true)
				app["stance"] = String(a.visual._stance_idle)
				appearances.append({"k": pair[0], "a": app})
		pack.append(e)
	if not appearances.is_empty():
		_appearances.rpc(appearances)
	var map := String(Game.current_map_id)
	var wire := NetCodec.pack_allies(pack)
	if is_host():
		_relay_allies(my_id(), map, wire)
	elif _peer and _peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED:
		_allies.rpc_id(1, map, wire)        # the room host forwards it to whoever needs it (bh-035)

## Where a player's hero stands, as far as the room host knows.
func _status_pos(id: int) -> Variant:
	if id == my_id():
		return (Game.player as Node3D).global_position if Game.player is Node3D and is_instance_valid(Game.player) else null
	var s: Dictionary = status.get(id, {})
	return s.get("pos", null)

## Room host (bh-035): forward one player's snapshot. Heroes near them on the same map get every snapshot, heroes far
## away on that map every ALLY_FAR_EVERY-th, and heroes elsewhere a slim presence update (their party frames, minimap
## rim and world map only read the hero's place and health) every ALLY_AWAY_EVERY-th.
func _relay_allies(from: int, map: String, wire: Array) -> void:
	var here: Variant = _status_pos(from)
	var slim: Array = []
	for to in _live_peers():
		if to == from or to == my_id() or not peers.has(to):
			continue
		var k := "%d>%d" % [from, to]
		var n: int = _relay_n.get(k, 0) + 1
		_relay_n[k] = n
		if _peer_map(to) != map:
			if n % ALLY_AWAY_EVERY != 1:
				continue
			if slim.is_empty():
				for e in wire:
					if e is Dictionary and e.get("k", "") == "p":
						slim.append({"k": "p", "b": e.b, "n": e.get("n", "Hero")})
			_ally_relay.rpc_id(to, from, map, slim)
			continue
		var there: Variant = _status_pos(to)
		if here is Vector3 and there is Vector3 and (here as Vector3).distance_to(there) > ALLY_NEAR and n % ALLY_FAR_EVERY != 1:
			continue
		_ally_relay.rpc_id(to, from, map, wire)

## Appearance must arrive reliably even when a large snapshot is overtaken by enemy updates.
@rpc("any_peer", "reliable")
func _appearances(pack: Array) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from) or not NetGuard.allow(from, "look", 4.0, 10.0) or pack.size() > NetGuard.MAX_ALLIES_PER_PACK:
		return
	for entry in pack:
		if entry is Dictionary and entry.get("k", null) is String and entry.get("a", null) is Dictionary and NetGuard.fits(entry.a, NetGuard.MAX_APPEARANCE_BYTES):
			var k := "%d:%s" % [from, entry.k]
			_appearance_cache[k] = entry.a
			_appearance_rev[k] = int(_appearance_rev.get(k, 0)) + 1

## A player's snapshot of their hero, Tempos and arena fighters, sent to the room host (bh-035: no longer broadcast).
@rpc("any_peer", "call_remote", "unreliable_ordered", 1)
func _allies(map: String, wire: Array) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not is_host() or not peers.has(from) or _peer_map(from) != map or not NetGuard.allow(from, "allies", 30.0, 60.0) 			or not NetGuard.fits(wire, NetGuard.MAX_PACK_BYTES):
		return
	var pack := NetCodec.unpack_allies(wire)
	if pack.size() != wire.size() or not NetGuard.ally_pack_ok(pack):
		return
	_take_allies(from, map, pack)
	_relay_allies(from, map, wire)

## The room host forwarding another player's snapshot (already checked there).
@rpc("authority", "call_remote", "unreliable_ordered", 1)
func _ally_relay(from: int, map: String, wire: Array) -> void:
	if not peers.has(from) or from == my_id() or _peer_map(from) != map:
		return
	var pack := NetCodec.unpack_allies(wire)
	if pack.size() != wire.size() or not NetGuard.ally_pack_ok(pack):
		return
	_take_allies(from, map, pack)

func _take_allies(from: int, map: String, pack: Array) -> void:
	for e in pack:
		if not e is Dictionary or not e.get("s", null) is Array:
			return
	for e in pack:
		if e.get("k", "") == "p" and (e.s as Array).size() >= 12:
			status[from] = {"map": map, "pos": e.s[0], "yaw": e.s[1], "hp": e.s[3], "mhp": e.s[4], "alive": e.s[5], "lvl": e.s[11],
				"t": Time.get_ticks_msec() * 0.001}
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
			if not _appearance_cache.has(k):
				continue                       # wait for the appearance
			var s: Array = e.s
			av = NetAvatar.new().setup(from, String(e.k), {"name": e.get("n", "Hero"), "lvl": s[11], "mhp": s[4], "hp": s[3]})
			av.arena_fighter = bool(e.get("af", false))
			Game.current_map.add_child(av)
			av.snap_to(s[0], s[1])
			_avatars[k] = av
		# re-dress only when a new appearance arrived (it used to rebuild the gear plan 15 times a second per ally)
		var rev := int(_appearance_rev.get(k, 0))
		if av.appearance_rev != rev and _appearance_cache.has(k):
			av.appearance_rev = rev
			av.set_appearance(_appearance_cache[k])
		av.guild_tag = String(e.get("g", ""))
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
	if n is Enemy and not (n as Enemy).net_replica and is_world_authority():
		_register_enemy.call_deferred(n)

func _register_existing_enemies() -> void:
	if Game.current_map == null:
		return
	for e in get_tree().get_nodes_in_group(&"enemy"):     # find_children cannot match script classes
		if e is Enemy and not e.net_replica and not e.is_queued_for_deletion() and Game.current_map.is_ancestor_of(e):
			_register_enemy(e)

func _register_enemy(e: Enemy) -> void:
	if not is_world_authority() or not is_instance_valid(e) or e.net_replica or e.is_queued_for_deletion() or not e.is_inside_tree():
		return
	var id := int(e.get_meta(&"net_id", _next_eid))
	if _host_enemies.get(id) == e:
		return
	_next_eid = maxi(_next_eid, id + 1)
	e.set_meta(&"net_id", id)
	_host_enemies[id] = e
	var map := String(Game.current_map_id)
	var epoch := _world_epoch
	e.tree_exiting.connect(func() -> void:
		if _host_enemies.get(id) != e:
			return
		_host_enemies.erase(id)
		if is_world_authority() and e.alive and not _unloading and _world_epoch == epoch:
			_enemy_gone.rpc(map, epoch, id))

static func enemy_info(e: Enemy) -> Dictionary:
	return {"id": int(e.get_meta(&"net_id")), "def": String(e.def.id), "lvl": e.level, "encounter_hp_mult": e.encounter_hp_mult, "mods": e.elite_mods.map(func(m): return String(m)),
		"diff": maxi(0, DataEnemies.DIFFICULTY.find(e.difficulty)), "mb": String(e.miniboss.get("id", "")), "flag": String(e.get_meta(&"boss_flag", "")),
		"pos": e.global_position, "yaw": e.rotation.y, "hp": e.hp,
		"depth_guardian": e.miniboss if e.has_meta(&"depth_guardian") else {},
		"dungeon_reward": float(e.get_meta(&"dungeon_reward_bonus", 0.0))}

## One monster's snapshot: [id, pos, yaw, vel, hp, max_hp, action, serial, rate, loop, engaged, shield]
static func enemy_state(id: int, e: Enemy) -> Array:
	var v := e.visual
	return [id, e.global_position, e.rotation.y, e.velocity, e.hp, e.max_hp(), String(v.current_action() if v else &""),
		v.action_serial if v else 0, v.action_rate if v else 1.0, bool(v._action_loop) if v else false, e.brain.is_engaged(), e.shield_hp]

## Has a monster changed enough since its last snapshot that the members would see the difference?
static func enemy_changed(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return true
	if (a[1] as Vector3).distance_squared_to(b[1]) > 0.0004 or absf(angle_difference(float(a[2]), float(b[2]))) > 0.02:
		return true
	if (a[3] as Vector3).distance_squared_to(b[3]) > 0.01:
		return true
	return a[4] != b[4] or a[5] != b[5] or a[6] != b[6] or a[7] != b[7] or a[9] != b[9] or a[10] != b[10] or a[11] != b[11]

## Stream the monsters near each member (bh-035): each state is built once per round, not once per member. A member is
## sent a monster when it changed since the snapshot that member last got (monsters beyond ENEMY_FAR of the member: on every
## ENEMY_FAR_EVERY-th round only), and otherwise once per ENEMY_KEEPALIVE so its replica never goes stale.
func _send_enemies() -> void:
	var here := String(Game.current_map_id)
	_enemy_tick += 1
	var now := Time.get_ticks_msec()
	var states := {}
	for id in _host_enemies:
		var e: Enemy = _host_enemies[id]
		if not is_instance_valid(e) or not e.alive:
			continue
		var s := enemy_state(id, e)
		states[id] = s
		var last: Variant = _enemy_last.get(id)
		if last == null or enemy_changed(last, s):
			_enemy_last[id] = s                # a new reference: members holding the old one are behind
	for id in _enemy_last.keys():
		if not states.has(id):
			_enemy_last.erase(id)
			for pid in _enemy_sent:
				(_enemy_sent[pid] as Dictionary).erase(id)
	for pid in peers:
		if pid == my_id() or _peer_map(pid) != here:
			continue
		var av := avatar(pid)
		var center: Vector3
		if av:
			center = av.global_position
		elif Game.player is Node3D and is_instance_valid(Game.player):
			center = (Game.player as Node3D).global_position
		else:
			continue                           # no hero on this machine and no avatar yet: nothing to measure range from
		var known: Dictionary = _known.get_or_add(pid, {})
		var sent: Dictionary = _enemy_sent.get_or_add(pid, {})
		var infos := []
		var out := []
		for id in states:
			var e: Enemy = _host_enemies[id]
			var d := e.global_position.distance_to(center)
			if d > ENEMY_RANGE:
				continue
			if not known.has(id):
				known[id] = true
				infos.append(enemy_info(e))
			var had: Array = sent.get(id, [-100000, null])
			var stale := now - int(had[0]) > ENEMY_KEEPALIVE * 1000.0
			var behind := not is_same(had[1], _enemy_last[id])
			var slow: bool = d > ENEMY_FAR or not (states[id][10] or states[id][6] != "")
			if not stale and (not behind or (slow and _enemy_tick % ENEMY_FAR_EVERY != 0)):
				continue
			sent[id] = [now, _enemy_last[id]]
			out.append(states[id])
		if not infos.is_empty():
			_enemy_spawn.rpc_id(pid, here, _world_epoch, infos)
		# unreliable packets above the MTU (~1392 bytes) are fragmented and lost more often (and the engine warns, which
		# costs the owner a frame), so a big snapshot goes out in packets of ENEMY_BATCH monsters
		for i in range(0, out.size(), ENEMY_BATCH):
			_enemy_states.rpc_id(pid, here, _world_epoch, NetCodec.pack_monsters(out.slice(i, i + ENEMY_BATCH)))

func _on_actor_died(actor: Node, killer: Node) -> void:
	if not is_world_authority() or not (actor is Enemy) or not actor.has_meta(&"net_id"):
		return
	_kill_checkpoint = true                    # one checkpoint for a whole AoE of kills, not one per monster
	var kp := 0
	if killer is NetAvatar:
		kp = (killer as NetAvatar).owner_peer
	elif killer is Player or killer is Tempo:
		kp = my_id()
	var e := actor as Enemy
	var here := String(Game.current_map_id)
	for pid in peers:
		if pid != my_id() and _peer_map(pid) == here and _known.get(pid, {}).has(int(e.get_meta(&"net_id"))):
			_enemy_died.rpc_id(pid, here, _world_epoch, int(e.get_meta(&"net_id")), kp, String(e.death_clip()))

## A client's hit on one of the host's monsters: the client resolved it (its hero, its skills); apply the numbers.
@rpc("any_peer", "reliable")
func _client_hit(map: String, epoch: int, eid: int, res: Dictionary, hit_point: Vector3, key: String) -> void:
	if not is_world_authority() or map != String(Game.current_map_id) or epoch != _world_epoch or _peer_map(multiplayer.get_remote_sender_id()) != map:
		return
	var e: Enemy = _host_enemies.get(eid)
	if e == null or not is_instance_valid(e) or not e.alive:
		return
	var from := multiplayer.get_remote_sender_id()
	if not NetGuard.allow(from, "hit", 40.0, 80.0) or not NetGuard.finite_vec(hit_point):
		return
	var av := avatar(from, key)
	if av == null:
		av = avatar(from, "p")
	if av == null or not av.alive:
		return
	# a reported hit has to come from a hero that is near the monster and near the point it claims
	if av.global_position.distance_to(e.global_position) > NetGuard.HIT_REACH or av.global_position.distance_to(hit_point) > NetGuard.HIT_REACH:
		return
	res = NetGuard.clean_result(res)
	if res.is_empty():
		return
	var result := NetCodec.decode_result(res)
	var req := DamageRequest.new()
	req.attacker = av.stats if av else null
	req.heavy = result.heavy
	req.tags = res.get("tags", {})
	e.ensure_stats()
	e._apply_result(result, req, av, hit_point)

## A monster hit a NetAvatar here on the host: the owner resolves it against the real hero or Tempo.
func forward_ally_hit(av: NetAvatar, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if not is_world_authority():
		return
	var src: Node = attacker
	if not (src is Enemy):
		return                                 # traps and hazards exist on the owner's map too: no double hits
	_ally_hit.rpc_id(av.owner_peer, String(Game.current_map_id), _world_epoch, av.key, NetCodec.encode_request(req), int(src.get_meta(&"net_id", 0)), hit_point)

# ---- Client: replicas ---------------------------------------------------------------------------------------------

@rpc("any_peer", "reliable")
func _enemy_spawn(map: String, epoch: int, infos: Array) -> void:
	if not _world_sender(map, epoch) or Game.current_map == null or infos.size() > 256:
		return
	for info in infos:
		if not info is Dictionary or not info.get("id", null) is int:
			continue
		var id := int(info.id)
		if _replicas.has(id) and is_instance_valid(_replicas[id]):
			continue
		var e := NetWorld.make_enemy(info, true)
		if e:
			_replicas[id] = e
			_replica_seen[id] = Time.get_ticks_msec() * 0.001

@rpc("any_peer", "call_remote", "unreliable_ordered", 2)
func _enemy_states(map: String, epoch: int, blob) -> void:
	if not _world_sender(map, epoch):
		return
	var states := NetCodec.unpack_monsters(blob)      # packed by the owner (bh-035); a malformed blob decodes to []
	var now := Time.get_ticks_msec() * 0.001
	for s in states:
		if not s is Array or (s as Array).size() < 12 or not NetGuard.finite_vec(s[1]) or not NetGuard.finite(s[4]):
			continue
		var e: Enemy = _replicas.get(int(s[0]))
		if e and is_instance_valid(e):
			e.net_apply(s)
			_replica_seen[int(s[0])] = now

@rpc("any_peer", "reliable")
func _enemy_died(map: String, epoch: int, eid: int, killer_peer: int, clip: String) -> void:
	if not _world_sender(map, epoch):
		return
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

@rpc("any_peer", "reliable")
func _enemy_gone(map: String, epoch: int, eid: int) -> void:
	if not _world_sender(map, epoch):
		return
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
			_forget_on_host.rpc_id(_world_owner, id)

@rpc("any_peer", "reliable")
func _forget_on_host(eid: int) -> void:
	# the client dropped a far replica: send its spawn info again when it comes back into range
	var from := multiplayer.get_remote_sender_id()
	if is_world_authority() and _known.has(from):
		(_known[from] as Dictionary).erase(eid)
		(_enemy_sent.get(from, {}) as Dictionary).erase(eid)

func _clear_replicas() -> void:
	for id in _replicas:
		if is_instance_valid(_replicas[id]):
			_replicas[id].queue_free()
	_replicas.clear()
	_replica_seen.clear()

## A local hero or Tempo hit a replica: show it here, let the host apply it.
func replica_hit(e: Enemy, result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if not _host_shared or not e.has_meta(&"net_id"):
		return
	var key := "p"
	if attacker is Tempo and (attacker as Tempo).data:
		key = "t%d" % (attacker as Tempo).data.uid
	var d := NetCodec.encode_result(result)
	d["tags"] = {&"push_dir": req.tags.get(&"push_dir", Vector3.ZERO), &"launch": req.tags.get(&"launch", 0.0)}
	_client_hit.rpc_id(_world_owner, String(Game.current_map_id), _world_epoch, int(e.get_meta(&"net_id")), d, hit_point if hit_point.is_finite() else e.center(), key)

## The host says a monster hit one of this machine's allies: resolve it against the real one.
@rpc("any_peer", "reliable")
func _ally_hit(map: String, epoch: int, key: String, req_d: Dictionary, attacker_eid: int, hit_point: Vector3) -> void:
	if not Game.in_session or not _world_sender(map, epoch):
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

# ---- bh-028: hero-against-hero hits in the Sand Arena -------------------------------------------------------------
# The attacker's machine knows the attacker (weapon, skills, crits); the owner's machine knows the target (armour,
# resistances, evasion, block). So the attacker resolves the offense against a bare target and sends the damage per
# element; the owner runs the defense half through the same pipeline (Actor._threat_guard adds the arena scaling and
# the cap there) and answers with the number that landed, which the attacker shows.

func _local_key(n: Node) -> String:
	if n is Player:
		return "p"
	if n is ArenaFighter and (n as ArenaFighter).data:
		return "a%d" % (n as ArenaFighter).data.uid
	if n is Tempo and (n as Tempo).data:
		return "t%d" % (n as Tempo).data.uid
	return ""

## The offense half of a hit on another machine's hero or adventurer, packed for the owner.
static func offense_pack(req: DamageRequest, target_level: int, rng_: RandomNumberGenerator) -> Dictionary:
	var pre := req.clone()
	var bare := DerivedStats.new()
	bare.level = target_level
	bare.loadout = WeaponLoadout.new()
	bare.values = {&"max_hp": 1000.0}
	# elemental penetration is applied once, by the defender against its real resistance (defense_request carries it):
	# the stand-in holds a matching resistance so this pass does not drive it negative and apply it a second time
	if req.attacker != null:
		for e in Elements.ELEMENTAL:
			var pv := req.attacker.get_stat(Elements.pen_key(e))
			if pv > 0.0:
				bare.values[Elements.res_key(e)] = pv
	pre.target = bare
	pre.target_status = null
	pre.evadable = false
	pre.blockable = false
	pre.tags.erase(&"blow_cap")
	var res := DamagePipeline.compute(pre, rng_)
	var comp := {}
	for e in res.components:
		if float(res.components[e]) > 0.0:
			comp[int(e)] = float(res.components[e])
	var atk := req.attacker
	var pens := {}
	if atk != null:
		for e in Elements.ELEMENTAL:
			var pv := atk.get_stat(Elements.pen_key(e))
			if pv > 0.0:
				pens[int(e)] = pv
	return {"c": comp, "ev": req.evadable, "bl": req.blockable, "crit": res.is_crit, "kb": req.knockback, "po": req.poise,
		"hv": req.heavy, "lbl": req.label, "lvl": atk.level if atk else target_level, "acc": atk.get_stat(&"accuracy", 30.0) if atk else 30.0,
		"pa": atk.get_stat(&"pen_armor") if atk else 0.0, "pe": pens, "st": req.direct_status,
		"push": req.tags.get(&"push_dir", Vector3.ZERO)}

## The defense half: a request that carries the packed damage through the target's own defenses.
static func defense_request(d: Dictionary) -> DamageRequest:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	var comp: Dictionary = d.get("c", {})
	var total := 0.0
	for e in comp:
		total += float(comp[e])
	req.base_min = total
	req.base_max = total
	req.use_weapon = false
	req.can_crit = false
	if total > 0.0:
		for e in comp:
			req.conversion[int(e)] = float(comp[e]) / total
	req.evadable = bool(d.get("ev", true))
	req.blockable = bool(d.get("bl", true))
	req.knockback = float(d.get("kb", 0.0))
	req.poise = float(d.get("po", 0.0))
	req.heavy = bool(d.get("hv", false))
	req.label = String(d.get("lbl", "Arena blow"))
	req.direct_status = d.get("st", {})
	req.tags[&"push_dir"] = d.get("push", Vector3.ZERO)
	req.tags[&"proc"] = true            # the offense (spell power, bonuses, the critical) is already in the numbers
	var atk := DerivedStats.new()
	atk.level = int(d.get("lvl", 1))
	atk.loadout = WeaponLoadout.new()
	atk.values = {&"accuracy": float(d.get("acc", 30.0)), &"pen_armor": float(d.get("pa", 0.0)), &"hero_source": 1.0,
		&"crit_damage": 1.5, &"impact_strength": 1.0}
	var pe: Dictionary = d.get("pe", {})
	for e in pe:
		atk.values[Elements.pen_key(int(e))] = float(pe[e])
	req.attacker = atk
	return req

## A local hero or adventurer hit another machine's hero or adventurer in the arena.
func resolved_hit(av: NetAvatar, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if not is_active() or av == null or req.attacker == null:
		return
	var akey := _local_key(attacker)
	var d := offense_pack(req, av.level, av.rng)
	_resolved_hit.rpc_id(av.owner_peer, String(Game.current_map_id), av.key, d, akey if akey != "" else "p",
		hit_point if hit_point.is_finite() else av.center())

@rpc("any_peer", "reliable")
func _resolved_hit(map: String, key: String, d: Dictionary, akey: String, hit_point: Vector3) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not Game.in_session or not peers.has(from) or map != String(Game.current_map_id):
		return
	var target: Actor = null
	for pair in _local_allies():
		if pair[0] == key:
			target = pair[1]
	if target == null or not target.alive:
		return
	var by: Node = avatar(from, akey)
	var res := target.receive_hit(defense_request(d), by, hit_point)
	if res == null:
		return
	if bool(d.get("crit", false)):
		res.is_crit = true
	_resolved_landed.rpc_id(from, map, key, res.total, res.is_crit, res.evaded, res.blocked, int(res.dominant_element), not target.alive, hit_point)

## The owner's answer: show the number that landed on their hero or adventurer.
@rpc("any_peer", "reliable")
func _resolved_landed(map: String, key: String, total: int, crit: bool, evaded: bool, blocked: bool, element: int, killed: bool, hit_point: Vector3) -> void:
	var from := multiplayer.get_remote_sender_id()
	if map != String(Game.current_map_id):
		return
	var av := avatar(from, key)
	if av == null:
		return
	var r := DamageResult.new()
	r.total = total
	r.is_crit = crit
	r.evaded = evaded
	r.blocked = blocked
	r.dominant_element = element
	Events.damage_dealt.emit(av, r, hit_point, Game.player)
	if killed and av.is_hero:
		Events.notify.emit("You defeated %s in the Sand Arena." % av.display_name, &"loot")

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
	if not Game.in_session or _peer_map(multiplayer.get_remote_sender_id()) != String(Game.current_map_id):
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

## Class Transcendence support (Bulwark Standard, Warden's Refuge, Sanctified Ground, Oath of Mercy) reaching another
## player's hero: the skill id, its status values, a heal share of their Maximum HP, a barrier share and a cleanse.
## The owner checks the skill and clamps everything (TranscendSkills.BARRIER_CAP, at most 3% healing per message).
func send_support(av: NetAvatar, sid: StringName, extra: Dictionary) -> void:
	if not is_active() or av == null or not is_instance_valid(av):
		return
	_ally_support.rpc_id(av.owner_peer, av.key, String(sid), extra)

@rpc("any_peer", "unreliable")
func _ally_support(key: String, sid: String, extra: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not Game.in_session or _peer_map(from) != String(Game.current_map_id) or not NetGuard.allow(from, "support", 12.0, 24.0):
		return
	if not NetGuard.fits(extra, 400):
		return
	if sid == "sig_dawn":
		_sig_dawn_heal(from, key, extra)
		return
	var s := DB.skill(StringName(sid))
	if s == null or not SUPPORT_SKILLS.has(s.id):
		return
	for pair in _local_allies():
		if pair[0] != key or not (pair[1] as Actor).alive:
			continue
		var a: Actor = pair[1]
		var time := clampf(float(extra.get("time", 0.0)), 0.0, 5.0)
		var vals: Variant = extra.get("vals", [])
		if vals is Array and (vals as Array).size() == s.aura_mods.size() and time > 0.0:
			var mods: Array = []
			for i in s.aura_mods.size():
				var m: Array = s.aura_mods[i]
				mods.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, clampf(float(vals[i]), -1.0, 1.0), s.display_name))
			a.status.apply(s.id, time, 1.0, 0.0, Elements.PHYSICAL, mods)
		var heal := clampf(float(extra.get("heal_pct", 0.0)), 0.0, 0.03)
		if heal > 0.0:
			a.heal(a.max_hp() * heal)
		var bar := clampf(float(extra.get("barrier_pct", 0.0)), 0.0, TranscendSkills.BARRIER_CAP)
		if bar > 0.0:
			TranscendSkills.give_barrier(a, a.max_hp() * bar, clampf(float(extra.get("time_b", extra.get("time", 6.0))), 0.5, 15.0), s)
		if int(extra.get("cleanse", 0)) > 0:
			TranscendSkills.cleanse_one(a)

## Dawnbringer (Grand Paladin signature) healing this machine's hero: only from a Grand Paladin, at most its share.
func _sig_dawn_heal(from: int, key: String, extra: Dictionary) -> void:
	if not DataTranscendence.ancestry(peer_class_id(from)).has(&"grand_paladin"):
		return
	var heal := clampf(float(extra.get("heal_pct", 0.0)), 0.0, DataTranscendence.sig(&"grand_paladin", "heal") / 100.0)
	for pair in _local_allies():
		if pair[0] == key and (pair[1] as Actor).alive and heal > 0.0:
			(pair[1] as Actor).heal((pair[1] as Actor).max_hp() * heal)

## Skills whose effects another player's machine accepts through _ally_support.
const SUPPORT_SKILLS := [&"rg_bulwark_standard", &"ww_wardens_refuge", &"gp_sanctified_ground", &"gp_oath_of_mercy"]

## Round-trip time to a peer in ms (the host sees every client; a client sees the host). -1 when unknown.
func ping_ms(peer: int) -> int:
	if _peer == null or not is_active():
		return -1
	var target := peer if is_host() else 1
	if target == my_id():
		return 0
	if not multiplayer.get_peers().has(target):
		return -1
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
		return is_world_authority() and not (source as Enemy).net_replica
	return source is Player or source is Tempo

## Shared effects from a roster member, at a sane rate.
func _fx_allowed() -> bool:
	var from := multiplayer.get_remote_sender_id()
	return peers.has(from) and NetGuard.allow(from, "fx", 40.0, 80.0)

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
	if not _fx_allowed():
		return
	if not (from.is_finite() and dir.is_finite() and is_finite(speed) and is_finite(reach) and is_finite(radius)) or look.length() > 48:
		return
	speed = clampf(speed, 0.0, 120.0)
	reach = clampf(reach, 0.0, 120.0)
	radius = clampf(radius, 0.0, 12.0)
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
	if not _fx_allowed() or not (at.is_finite() and dir.is_finite()) or not NetGuard.fits(extra, 600):
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
		"tzone":
			TranscendZone.remote(FX.world, at, String(extra.get("z", "")), float(extra.get("r", 4.0)), float(extra.get("d", 5.0)), StringName(String(extra.get("c", ""))))
		"tsnare":
			var pts: Variant = extra.get("pts", [])
			if pts is Array:
				SnareLine.remote(FX.world, pts, float(extra.get("d", 10.0)), float(extra.get("t", 1.1)))
		"tring":
			var th := ClassTranscendence.class_theme(StringName(String(extra.get("c", ""))))
			FX.spawn(VFXLib.ring_wave(Color(th.accent, 0.85), clampf(float(extra.get("r", 6.0)), 0.5, 10.0), 0.5, 0.8), at)
		"tpatch":
			AreaEffects.hazard(FX.world, at, clampf(float(extra.get("r", 3.0)), 0.5, 6.0), clampf(float(extra.get("d", 4.0)), 0.5, 10.0), null, null, 0, Color(0.4, 0.62, 0.32), 0.5)
		"barrage":
			AbyssMoves.remote_barrage(at, dir, extra)
		"curse":
			AbyssMoves.remote_curse(at, extra)
		"veil":
			var radius := float(extra.get("r", 6.0))
			FX.spawn(VFXLib.particles(Color(0.35, 0.33, 0.38, 0.75), 70, 2.2, true, 1.6, 2.5, 180.0, Vector3(0, 0.4, 0), radius * 0.5, false), at + Vector3.UP * 0.6)
			FX.spawn(VFXLib.ring_wave(Color(0.5, 0.4, 0.65, 0.7), radius, 0.5), at)

## Class Transcendence signature bursts (ClassSignature): Royal Retort, Dawnbringer, Collapse ... happened. Only the kind
## and two points travel; the receiver draws them and accepts only the bursts of a trait the sender's validated class
## line has.
func share_class_sig(kind: String, n: int, at: Vector3, to: Vector3) -> void:
	if not is_active():
		return
	_remote_class_sig.rpc(String(Game.current_map_id), kind, n, at, to)

@rpc("any_peer", "unreliable")
func _remote_class_sig(map: String, kind: String, n: int, at: Vector3, to: Vector3) -> void:
	if map != String(Game.current_map_id) or FX.world == null or Game.travelling:
		return
	if not _fx_allowed() or kind.length() > 16 or not (at.is_finite() and to.is_finite()):
		return
	var from := multiplayer.get_remote_sender_id()
	var av := avatar(from)
	if av == null or av.arena_fighter:
		return
	var k := StringName(kind)
	if not ClassSignature.allowed(peer_class_id(from), k):
		return
	var sig := av.get_node_or_null(^"ClassSignature") as ClassSignature
	if sig == null:
		return
	if at.distance_to(av.global_position) <= 40.0 and to.distance_to(av.global_position) <= 60.0:
		sig.burst(k, at, to)

## bh-033: an arena fixture changed on the map owner's machine (a pillar broke): every player on the map applies it.
func arena_event(kind: StringName, idx: int, data: Dictionary = {}) -> void:
	if not is_active() or not is_world_authority():
		return
	var here := String(Game.current_map_id)
	for pid in peers:
		if pid != my_id() and _peer_map(pid) == here:
			_arena_event.rpc_id(pid, here, _world_epoch, String(kind), idx, data)
	if kind == &"pillar":
		_send_checkpoint.call_deferred()

## The owner's arena change, applied on this machine: a pillar breaks (state, also in checkpoints) or a rot patch
## appears (visual only here: the owner's copy does the damage).
@rpc("any_peer", "reliable")
func _arena_event(map: String, epoch: int, kind: String, idx: int, data: Dictionary) -> void:
	if not _world_sender(map, epoch) or Game.current_map == null or FX.world == null:
		return
	match kind:
		"pillar":
			if idx >= 0 and idx <= 63:
				ArenaState.break_pillar(Game.current_map, idx)
		"rot":
			var at = data.get("at", null)
			var r := clampf(float(data.get("r", 4.0)), 0.5, 8.0)
			var d := clampf(float(data.get("d", 20.0)), 1.0, 60.0)
			if at is Vector3 and (at as Vector3).is_finite() and get_tree().get_nodes_in_group(&"rot_patch").size() < 8:
				var h := AreaEffects.hazard(FX.world, at, r, d, null, null, 0, Color(0.5, 0.75, 0.12), 0.6)
				h.add_to_group(&"rot_patch")

func share_telegraph(pos: Vector3, radius: float, delay: float, color: Color, shape: String, inner: float, source: Node) -> void:
	if not is_active() or not owns_source(source):
		return
	_remote_telegraph.rpc(String(Game.current_map_id), pos, radius, delay, color, shape, inner)

@rpc("any_peer", "unreliable")
func _remote_telegraph(map: String, pos: Vector3, radius: float, delay: float, color: Color, shape: String, inner: float) -> void:
	if map != String(Game.current_map_id) or FX.world == null or Game.travelling:
		return
	if not _fx_allowed():
		return
	if not (pos.is_finite() and is_finite(radius) and is_finite(delay) and is_finite(inner)) or shape.length() > 24:
		return
	radius = clampf(radius, 0.0, 40.0)
	delay = clampf(delay, 0.0, 10.0)
	inner = clampf(inner, 0.0, radius)
	AreaEffects.delayed(FX.world, pos, radius, delay, null, null, 0, color, shape, inner)

# ---- Chat ---------------------------------------------------------------------------------------------------------

func send_chat(text: String) -> void:
	if not is_active():
		return
	var clean := ChatText.clean(text)
	if clean.is_empty() or Cheats.is_code(clean):
		return
	chat_received.emit(my_id(), clean)
	_chat.rpc(clean)

@rpc("any_peer", "reliable")
func _chat(text: String) -> void:
	var from := multiplayer.get_remote_sender_id()
	if NetGuard.allow(from, "chat", 1.0, 5.0):
		receive_chat(from, text)

## Resolve identity from the connected roster, never from a supplied display name.
func receive_chat(peer: int, text: String) -> void:
	var clean := ChatText.clean(text)
	if not is_active() or not peers.has(peer) or clean.is_empty() or Cheats.is_code(clean):
		return
	chat_received.emit(peer, clean)

func _chat_system(text: String, notice := false) -> void:
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.chat.add_line(text, UITheme.GOLD)
	if notice:
		Events.notify.emit(text, &"info")
	if is_host():
		for id in _live_peers():
			_chat_sys_remote.rpc_id(id, text, notice)

@rpc("authority", "reliable")
func _chat_sys_remote(text: String, notice := false) -> void:
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.chat.add_line(text, UITheme.GOLD)
	if notice:
		Events.notify.emit(text, &"info")

# ---- Profile updates (bh-011) -------------------------------------------------------------------------------------

## Tell the others this hero's level / map changed (party frames, name plates).
func update_profile() -> void:
	if not is_active() or connecting:
		return
	if is_host():
		peers[1] = _profile()
		_rpc_peers()
		roster_updated.emit()
	else:
		_profile_changed.rpc_id(1, _profile())

@rpc("any_peer", "reliable")
func _profile_changed(profile: Dictionary) -> void:
	var id := multiplayer.get_remote_sender_id()
	if not is_host() or not peers.has(id) or not NetGuard.allow(id, "profile", 2.0, 6.0):
		return
	profile = NetGuard.clean_profile(profile)
	if profile.is_empty():
		return
	profile.erase("ticket")
	var keep: String = peers[id].get("map", "")
	var claimed_path := String(profile.get("path", ""))
	if dedicated:
		for field in ["name", "cls", "userid", "character", "path"]:
			profile[field] = peers[id].get(field, "")
		profile["level"] = clampi(int(profile.get("level", 1)), 1, BH.LEVEL_CAP)
	peers[id] = profile
	if keep != "":
		peers[id]["map"] = keep
	_rpc_peers()
	roster_updated.emit()
	# Official: a new class advancement shows once the account service holds it in an acknowledged save (the client
	# sends its profile after the save is confirmed; the coordinator reads the stored character, not the claim)
	if dedicated and claimed_path != String(peers[id].get("path", "")):
		_refresh_official_identity(id)

func _refresh_official_identity(id: int) -> void:
	var lease := String(_server_leases.get(id, ""))
	if lease == "":
		return
	var result := await _server_request("/internal/character", {"lease": lease})
	if result.has("error") or not peers.has(id):
		return
	var character: Dictionary = result.get("character", {})
	peers[id]["path"] = String(character.get("path", ""))
	peers[id]["level"] = clampi(int(character.get("level", peers[id].get("level", 1))), 1, BH.LEVEL_CAP)
	_rpc_peers()
	roster_updated.emit()

# ---- Party travel requests (bh-011; unused since bh-015, when clients started travelling on their own) ---------------

## A client stepped through a door / onto a waypoint / read a scroll: ask the host to take the party there.
## req: {"kind": "travel" | "door" | "point", "map": id, "spawn": id, "pos": Vector3, "yaw": float}. True when asked.
func request_travel(req: Dictionary) -> bool:
	if not is_client() or connecting:
		return false
	var map := StringName(req.get("map", ""))
	if map == Game.current_map_id and String(req.get("kind", "travel")) != "point":
		return false
	var now := Time.get_ticks_msec() * 0.001
	if now - _travel_asked_t < 6.0:
		Events.notify.emit("Waiting for %s to answer." % host_name(), &"info")
		return false
	_travel_asked_t = now
	_travel_request.rpc_id(1, req)
	Events.notify.emit("Asked %s to lead the party to %s." % [host_name(), place_name(map)], &"info")
	return true

func host_name() -> String:
	return String(peers.get(1, {}).get("name", "the host"))

static func place_name(map: StringName) -> String:
	var d := DB.map_def(map)
	return d.display_name if d else String(map)

## The travel request the host is being asked about ({} when none).
func pending_travel() -> Dictionary:
	return _travel_pending

@rpc("any_peer", "reliable")
func _travel_request(req: Dictionary) -> void:
	if not is_host() or not Game.in_session:
		return
	var from := multiplayer.get_remote_sender_id()
	var map := StringName(req.get("map", ""))
	if DB.map_def(map) == null or not peers.has(from):
		return
	if not _travel_pending.is_empty():
		_travel_answer.rpc_id(from, false, "%s is answering another request." % String(peers[1].name))
		return
	_travel_pending = {"from": from, "req": req, "t": Time.get_ticks_msec()}
	var serial: int = _travel_pending.t
	var who: String = peers[from].get("name", "A hero")
	Audio.play_ui(&"ui_open")
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.confirm.ask("Party Travel", "%s wants the party to go to %s. Everyone follows you." % [who, place_name(map)],
			func() -> void: answer_travel(true), "Go", false, null, "Stay")
		var c: Node = Game.ui_root.confirm
		if c.has_signal(&"cancelled"):
			c.connect(&"cancelled", func() -> void:
				if _travel_pending.get("t", -1) == serial:
					answer_travel(false), CONNECT_ONE_SHOT)
	# nobody answered in time: the request lapses
	get_tree().create_timer(20.0).timeout.connect(func() -> void:
		if _travel_pending.get("t", -1) == serial:
			if Game.ui_root and is_instance_valid(Game.ui_root) and Game.ui_root.confirm.visible:
				Game.ui_root.confirm.visible = false
			answer_travel(false, "%s did not answer." % host_name().capitalize()))

## The host's answer to the pending request: Go travels (everyone follows), Stay tells the asker.
func answer_travel(go: bool, why := "") -> void:
	if not is_host() or _travel_pending.is_empty():
		return
	var from: int = _travel_pending.from
	var req: Dictionary = _travel_pending.req
	_travel_pending = {}
	if peers.has(from):
		_travel_answer.rpc_id(from, go, why if why != "" else ("" if go else "%s wants to stay here for now." % String(peers[1].name)))
	if not go:
		return
	_chat_system("The party travels to %s." % place_name(StringName(req.map)), true)
	match String(req.get("kind", "travel")):
		"door": Game.door_travel(StringName(req.map), StringName(req.get("spawn", "start")))
		"point": Game.travel_to_point(StringName(req.map), req.get("pos", Vector3.ZERO), float(req.get("yaw", 0.0)))
		_: Game.travel(StringName(req.map), StringName(req.get("spawn", "start")))

@rpc("authority", "reliable")
func _travel_answer(go: bool, why: String) -> void:
	_travel_asked_t = -99.0
	if not go and why != "":
		Events.notify.emit(why, &"info")

# ---- Team Portal -------------------------------------------------------------------------------------------------

const PORTAL_CAST := 1.25
const PORTAL_COOLDOWN := 10.0
const PORTAL_TIMEOUT := 5.0
var _portal_pending := {}
var _portal_serial := 0
var _portal_ready_at := 0.0

## Members travel to the leader. The leader chooses a member in Multiplayer (or clicks their party frame).
func open_team_portal() -> void:
	if (is_host() or official_room) and Game.ui_root:
		Game.ui_root.open(&"multiplayer")
	else:
		team_portal(1)

func portal_error(target: int) -> String:
	if not is_active() or connecting:
		return "Join a party first."
	if target == my_id() or not peers.has(target):
		return "Choose another party member."
	if not is_host() and not official_room and target != 1:
		return "Team Portal takes you to the party leader."
	if Game.travelling or following or not Game.in_session:
		return "Finish travelling first."
	var p := Game.player as Player
	if p == null or not p.alive:
		return "Get back on your feet first."
	if in_trade():
		return "Finish or cancel your trade first."
	if not _portal_pending.is_empty():
		return "Team Portal is already being cast."
	var remaining := _portal_ready_at - Time.get_ticks_msec() * 0.001
	if remaining > 0.0:
		return "Team Portal is ready in %d seconds." % ceili(remaining)
	return ""

func team_portal(target := 1) -> bool:
	var error := portal_error(target)
	if error != "":
		Events.notify.emit(error, &"info")
		return false
	_portal_serial += 1
	var p := Game.player as Player
	_portal_pending = {"target": target, "serial": _portal_serial, "map": Game.current_map_id,
		"pos": p.global_position, "hp": p.hp, "phase": "cast"}
	Events.notify.emit("Casting Team Portal to %s. Stand still for a moment." % peers[target].get("name", "your ally"), &"info")
	FX.spawn(VFXLib.ring_wave(Color(0.55, 0.9, 1.0, 0.9), 2.0, PORTAL_CAST), p.global_position)
	_finish_portal_cast(_portal_serial)
	return true

func _portal_cancel(why: String) -> void:
	_portal_pending = {}
	_portal_serial += 1
	Events.notify.emit(why, &"info")

func _portal_tick() -> void:
	if _portal_pending.is_empty():
		return
	var p := Game.player as Player
	if not peers.has(int(_portal_pending.target)):
		_portal_cancel("Team Portal cancelled: that player left.")
	elif p == null or not p.alive or Game.travelling or Game.current_map_id != _portal_pending.map:
		_portal_cancel("Team Portal cancelled.")
	elif p.global_position.distance_to(_portal_pending.pos) > 0.8 or p.hp < float(_portal_pending.hp):
		_portal_cancel("Team Portal interrupted by movement or damage.")

func _finish_portal_cast(serial: int) -> void:
	await get_tree().create_timer(PORTAL_CAST).timeout
	_portal_tick()
	if _portal_pending.get("serial", -1) != serial:
		return
	_portal_pending["phase"] = "waiting"
	_portal_request.rpc_id(int(_portal_pending.target), serial)
	await get_tree().create_timer(PORTAL_TIMEOUT).timeout
	if _portal_pending.get("serial", -1) == serial:
		_portal_cancel("Team Portal timed out. Try again when your ally has finished travelling.")

@rpc("any_peer", "reliable")
func _portal_request(serial: int) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from) or (not is_host() and not official_room and from != 1):
		return
	var p := Game.player as Player
	var error := ""
	if not Game.in_session or Game.travelling or following or p == null:
		error = "Your ally is travelling. Try again in a moment."
	elif in_trade():
		error = "Your ally is trading. Try again when they finish."
	_portal_destination.rpc_id(from, serial, error, String(Game.current_map_id), p.global_position if p else Vector3.ZERO, p.rotation.y if p else 0.0)

@rpc("any_peer", "reliable")
func _portal_destination(serial: int, error: String, map: String, pos: Vector3, yaw: float) -> void:
	if _portal_pending.get("serial", -1) != serial or int(_portal_pending.get("target", 0)) != multiplayer.get_remote_sender_id():
		return
	_portal_tick()
	if _portal_pending.is_empty():
		return
	if error != "":
		_portal_cancel(error)
		return
	if DB.map_def(StringName(map)) == null or not pos.is_finite() or not is_finite(yaw):
		_portal_cancel("Team Portal destination is unavailable.")
		return
	var target := int(_portal_pending.target)
	_portal_pending = {}
	_portal_ready_at = Time.get_ticks_msec() * 0.001 + PORTAL_COOLDOWN
	await _portal_travel(StringName(map), pos, yaw)
	if is_active() and peers.has(target):
		Events.notify.emit("Team Portal: arrived beside %s." % peers[target].get("name", "your ally"), &"info")

## Use the ally's floor height, not a ray from above roofs or bridges.
func portal_arrival(pos: Vector3, yaw: float) -> Vector3:
	if Game.current_map and Game.current_map.is_inside_tree():
		return Loot.landing_point(Game.current_map.get_world_3d(), pos, -yaw, 1.8) + Vector3.UP * 0.05
	return pos

func _portal_travel(map: StringName, pos: Vector3, yaw: float) -> void:
	if map != Game.current_map_id:
		await _follow(map, pos, yaw)
	else:
		var pl := Game.player as Player
		var spot := portal_arrival(pos, yaw)
		pl.teleport_to(spot)
		pl.on_teleported()
		TempoParty.regroup(pl)
	if Game.player and is_instance_valid(Game.player):
		FX.spawn(VFXLib.light_pillar(Color(0.55, 0.9, 1.0), 4.0, 0.8, 0.6), Game.player.global_position)
		Audio.play_at(&"teleport_whoosh", Game.player.global_position, -4.0)
		Game.save_now()

## Existing respawn and summons paths use the same checked, voluntary cast.
func regroup() -> void:
	team_portal(1)

# ---- Summon the party (bh-015) -------------------------------------------------------------------------------------

## Host: ask every player who is not already beside you to come to your side. Returns how many were asked.
func summon_party() -> int:
	if not is_host() or not Game.in_session or Game.travelling:
		return 0
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p):
		return 0
	var now := Time.get_ticks_msec() * 0.001
	if now - _summon_t < SUMMON_COOLDOWN:
		Events.notify.emit("The last summons is still being answered.", &"info")
		return 0
	var asked := 0
	for pid in peers:
		if int(pid) == 1:
			continue
		var av := avatar(int(pid))
		if av and av.global_position.distance_to(p.global_position) < BESIDE_M:
			continue
		_summoned.rpc_id(int(pid), String(Game.current_map_id))
		asked += 1
	if asked == 0:
		Events.notify.emit("Everyone is already at your side." if peers.size() > 1 else "Nobody has joined yet.", &"info")
		return 0
	_summon_t = now
	_chat_system("%s summons the party to %s." % [String(peers.get(1, {}).get("name", "The host")), place_name(Game.current_map_id)], true)
	return asked

## Client: the host summons the party. Go / Stay (no answer in SUMMON_WAIT seconds is Stay).
@rpc("authority", "reliable")
func _summoned(map: String) -> void:
	if not is_client() or not Game.in_session:
		return
	var serial := Time.get_ticks_msec()
	_summon = {"map": map, "t": serial}
	Audio.play_ui(&"ui_open")
	var here := StringName(map) == Game.current_map_id
	var text := "%s summons the party to %s. Go to their side?" % [host_name(), "this place" if here else place_name(StringName(map))]
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.confirm.ask("Summoned", text, func() -> void: answer_summon(true), "Go", false, null, "Stay")
		var c: Node = Game.ui_root.confirm
		if c.has_signal(&"cancelled"):
			c.connect(&"cancelled", func() -> void:
				if _summon.get("t", -1) == serial:
					answer_summon(false), CONNECT_ONE_SHOT)
	Events.notify.emit(text, &"info")
	get_tree().create_timer(SUMMON_WAIT).timeout.connect(func() -> void:
		if _summon.get("t", -1) == serial:
			if Game.ui_root and is_instance_valid(Game.ui_root) and Game.ui_root.confirm.visible:
				Game.ui_root.confirm.visible = false
			answer_summon(false))

## Client: answer the pending summons. Go asks the host where it stands now and travels there.
func answer_summon(go: bool) -> void:
	if _summon.is_empty():
		return
	_summon = {}
	var p := Game.player as Player
	if go and (p == null or not p.alive):
		Events.notify.emit("Get back on your feet first.", &"info")
		go = false
	_summon_reply.rpc_id(1, go)
	if go:
		team_portal(1)

func pending_summon() -> Dictionary:
	return _summon

@rpc("any_peer", "reliable")
func _summon_reply(go: bool) -> void:
	if not is_host():
		return
	var who: String = peers.get(multiplayer.get_remote_sender_id(), {}).get("name", "A hero")
	Events.notify.emit(("%s is on the way." if go else "%s stays where they are.") % who, &"info")

# ---- Revive (bh-011) ----------------------------------------------------------------------------------------------

## This machine's hero stands beside a fallen friend and revives them.
func revive(av: NetAvatar) -> void:
	if not is_active() or av == null or not is_instance_valid(av) or av.alive or not av.is_hero:
		return
	var h := Game.hero
	_revived.rpc_id(av.owner_peer, h.hero_name if h else "A friend")
	FX.spawn(VFXLib.light_pillar(Color(1.0, 0.9, 0.55), 5.0, 1.0, 0.8), av.global_position)
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.5, 0.9), 3.0, 0.6), av.global_position)
	Audio.play_at(&"holy_chime", av.global_position)
	Events.notify.emit("You revived %s." % av.display_name, &"info")

@rpc("any_peer", "reliable")
func _revived(_by: String) -> void:
	var from := multiplayer.get_remote_sender_id()
	var av := avatar(from)
	var p := Game.player as Player
	if not peers.has(from) or _peer_map(from) != String(Game.current_map_id) or av == null or not av.alive or p == null:
		return
	if av.global_position.distance_to(p.global_position) > 5.0:
		return
	revive_local(String(peers[from].get("name", "A friend")))

## Stand this machine's fallen hero up where they fell (a friend's revive).
func revive_local(by: String) -> bool:
	var p := Game.player as Player
	if p == null or not is_instance_valid(p) or p.alive or not Game.in_session:
		return false
	p.respawn()
	p.hp = p.max_hp() * REVIVE_HP
	p.health_changed.emit(p.hp, p.max_hp())
	if Game.ui_root and is_instance_valid(Game.ui_root) and Game.ui_root.pause_menu.visible:
		Game.ui_root.pause_menu.close()
	FX.spawn(VFXLib.light_pillar(Color(1.0, 0.9, 0.55), 5.0, 1.0, 0.8), p.global_position)
	Audio.play_at(&"holy_chime", p.global_position)
	Events.player_respawned.emit()
	Events.notify.emit("%s revived you!" % by, &"loot")
	return true

# ---- Trade (bh-016) -------------------------------------------------------------------------------------------------

func in_trade() -> bool:
	return not trade.is_empty()

## "" when a trade request to `peer` can be sent now, otherwise why not.
func trade_error(peer: int) -> String:
	if not is_active() or connecting:
		return "Trading needs a multiplayer game."
	if peer == my_id() or not peers.has(peer):
		return "Nobody by that name is in the party."
	if not Game.in_session or Game.hero == null or Game.travelling:
		return "You cannot trade right now."
	if in_trade():
		return "You are already trading."
	var p := Game.player as Player
	if p == null or not p.alive:
		return "You cannot trade while fallen."
	if Time.get_ticks_msec() * 0.001 - _trade_asked_t < 3.0:
		return "Wait a moment before asking again."
	return ""

## Ask "Send a Trade Request?" for an ally (clicking them, their party frame, the Multiplayer window).
func trade_prompt(peer: int) -> void:
	var err := trade_error(peer)
	if err != "":
		Events.notify.emit(err, &"error")
		return
	var info: Dictionary = peers[peer]
	Game.ui_root.ask("Trade", "Send %s (Level %d %s) a Trade Request?\nYou each choose items and gold; nothing changes hands until you both accept." % [
			info.get("name", "this hero"), int(info.get("level", 1)), peer_class_name(peer)],
		func() -> void: request_trade(peer), "Send Request")

## Send `peer` a Trade Request. Returns "" or the reason it was not sent.
func request_trade(peer: int) -> String:
	var err := trade_error(peer)
	if err != "":
		Events.notify.emit(err, &"error")
		return err
	_trade_asked_t = Time.get_ticks_msec() * 0.001
	var who := String(peers[peer].get("name", "that hero"))
	trade = {"peer": peer, "name": who, "phase": "asking", "mine": {"gold": 0, "items": []}, "theirs": {"gold": 0, "items": []},
		"rev": 0, "their_rev": 0, "my_ok": false, "their_ok": false, "committing": false, "their_ready": false, "sent": {}}
	_trade_ask.rpc_id(peer, String(Game.hero.hero_name))
	Events.notify.emit("Trade Request sent to %s." % who, &"info")
	trade_changed.emit()
	var serial := _trade_asked_t
	get_tree().create_timer(35.0).timeout.connect(func() -> void:
		if in_trade() and trade.phase == "asking" and _trade_asked_t == serial:
			trade_cancel("%s did not answer." % who))
	return ""

@rpc("any_peer", "reliable")
func _trade_ask(who: String) -> void:
	if not is_active():
		return
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from):
		return
	var p := Game.player as Player
	if not Game.in_session or Game.travelling or in_trade() or not _trade_incoming.is_empty() or p == null or not p.alive \
			or Game.ui_root == null or not is_instance_valid(Game.ui_root):
		_trade_reply.rpc_id(from, false, "%s cannot trade right now." % String(peers.get(my_id(), {}).get("name", "That hero")))
		return
	var serial := Time.get_ticks_msec()
	_trade_incoming = {"peer": from, "name": who, "t": serial}
	Audio.play_ui(&"ui_open")
	var info: Dictionary = peers[from]
	var box: ConfirmDialog = _request_box()
	_drop_request_hooks(box)
	box.ask("Trade Request", "%s (Level %d) wants to trade with you. Gold and items are swapped only when you both accept the same offers." % [
			who, int(info.get("level", 1))],
		func() -> void: _trade_answer(true, serial), "Accept", false, null, "Decline")
	box.connect(&"cancelled", func() -> void: _trade_answer(false, serial), CONNECT_ONE_SHOT)
	Events.notify.emit("%s wants to trade." % who, &"info")
	get_tree().create_timer(30.0).timeout.connect(func() -> void:
		if _trade_incoming.get("t", -1) == serial:
			if Game.ui_root and is_instance_valid(Game.ui_root) and _request_box().visible:
				_request_box().visible = false
			_trade_answer(false, serial))

## bh-041: the box that asks about other players' requests (its own, so no other question can replace it).
func _request_box() -> ConfirmDialog:
	return Game.ui_root.request_box if Game.ui_root.get(&"request_box") != null else Game.ui_root.confirm

## Forget a previous request's "Decline" hook (a request that was accepted never fired its one-shot).
func _drop_request_hooks(box: ConfirmDialog) -> void:
	for c in box.cancelled.get_connections():
		box.cancelled.disconnect(c.callable)

func _trade_answer(go: bool, serial: int) -> void:
	if _trade_incoming.get("t", -1) != serial:
		return
	if Game.ui_root and is_instance_valid(Game.ui_root):
		_drop_request_hooks(_request_box())
	var from: int = _trade_incoming.peer
	var who: String = _trade_incoming.name
	_trade_incoming = {}
	if not peers.has(from):
		return
	var p := Game.player as Player
	if go and (in_trade() or p == null or not p.alive):
		go = false
	_trade_reply.rpc_id(from, go, "" if go else "%s declined the trade." % String(peers.get(my_id(), {}).get("name", "That hero")))
	if go:
		trade = {"peer": from, "name": who, "phase": "open", "mine": {"gold": 0, "items": []}, "theirs": {"gold": 0, "items": []},
			"rev": 0, "their_rev": 0, "my_ok": false, "their_ok": false, "committing": false, "their_ready": false, "sent": {}}
		trade_changed.emit()
		Game.ui_root.open(&"trade")

@rpc("any_peer", "reliable")
func _trade_reply(go: bool, why: String) -> void:
	if not in_trade() or int(trade.peer) != multiplayer.get_remote_sender_id() or trade.phase != "asking":
		return
	if not go:
		trade_reset(why if why != "" else "%s declined the trade." % trade.name)
		return
	trade.phase = "open"
	trade_changed.emit()
	Game.ui_root.open(&"trade")

## Put `gold` and `items` (ItemInstances from your bag) on the table. Clears both acceptances. Returns "" or why not.
func trade_set_offer(gold: int, items: Array) -> String:
	if not in_trade() or trade.phase != "open" or trade.committing:
		return "There is no open trade."
	var offer := {"gold": gold, "items": items}
	var err := TradeRules.offer_error(Game.hero, offer)
	if err != "":
		return err
	trade.mine = offer
	trade.rev = int(trade.rev) + 1
	trade.my_ok = false
	trade.their_ok = false
	trade.sent = TradeRules.to_wire(offer)
	trade.mine["wire"] = trade.sent
	_trade_offer.rpc_id(int(trade.peer), int(trade.rev), trade.sent)
	trade_changed.emit()
	return ""

@rpc("any_peer", "reliable")
func _trade_offer(rev: int, wire: Dictionary) -> void:
	if not in_trade() or int(trade.peer) != multiplayer.get_remote_sender_id() or trade.phase != "open" or trade.committing:
		return
	if not NetGuard.fits(wire, NetGuard.MAX_TRADE_BYTES):
		return
	trade.theirs = TradeRules.read_incoming(wire)
	trade.their_rev = rev
	trade.my_ok = false
	trade.their_ok = false
	Audio.play_ui(&"ui_click")
	trade_changed.emit()

## Accept (or take back the acceptance of) the two offers as they stand.
func trade_accept(on: bool) -> void:
	if not in_trade() or trade.phase != "open" or trade.committing:
		return
	if on:
		var err := TradeRules.swap_error(Game.hero, trade.mine, trade.theirs)
		if err != "":
			Events.notify.emit(err, &"error")
			return
	trade.my_ok = on
	_trade_ok.rpc_id(int(trade.peer), on, int(trade.rev), int(trade.their_rev))
	trade_changed.emit()
	_trade_check()

@rpc("any_peer", "reliable")
func _trade_ok(on: bool, their_rev: int, my_rev_seen: int) -> void:
	if not in_trade() or int(trade.peer) != multiplayer.get_remote_sender_id() or trade.phase != "open" or trade.committing:
		return
	# only counts when it was given for the very offers on the table here
	if their_rev != int(trade.their_rev) or my_rev_seen != int(trade.rev):
		return
	trade.their_ok = on
	trade_changed.emit()
	_trade_check()

## Both accepted: check this hero can honour it, tell the other side, and swap once both are ready.
func _trade_check() -> void:
	if not in_trade() or not trade.my_ok or not trade.their_ok or trade.committing:
		return
	var err := TradeRules.swap_error(Game.hero, trade.mine, trade.theirs)
	if err == "" and TradeRules.to_wire(trade.mine) != trade.sent:
		err = "Your offer changed while the trade was open."
	if err != "":
		trade_cancel(err)
		return
	trade.committing = true
	trade["server_nonce"] = Crypto.new().generate_random_bytes(16).hex_encode() if Official.active else ""
	_trade_ready.rpc_id(int(trade.peer), String(trade.server_nonce))
	trade_changed.emit()
	_trade_finish()

@rpc("any_peer", "reliable")
func _trade_ready(nonce := "") -> void:
	if not in_trade() or int(trade.peer) != multiplayer.get_remote_sender_id():
		return
	trade.their_ready = true
	trade["their_nonce"] = nonce
	_trade_finish()

func _trade_finish() -> void:
	if not in_trade() or not trade.committing or not trade.their_ready:
		return
	var mine: Dictionary = trade.mine
	var theirs: Dictionary = trade.theirs
	var who: String = trade.name
	if Official.active:
		if trade.get("server_finishing", false):
			return
		trade["server_finishing"] = true
		var other := String(peers.get(int(trade.peer), {}).get("character", ""))
		var own_nonce := String(trade.get("server_nonce", ""))
		var their_nonce := String(trade.get("their_nonce", ""))
		if other == "" or own_nonce.length() != 32 or their_nonce.length() != 32:
			trade_cancel("Official trade identity is missing.")
			return
		var identities := [Official.character_id + ":" + own_nonce, other + ":" + their_nonce]
		identities.sort()
		var trade_id := "|".join(identities).sha256_text()
		trade["trade_id"] = trade_id
		trade["other_character"] = other
		# where each offered item sits in the bag (the confirmed save is a copy of this bag)
		var index := {}
		var items: Array = mine.get("items", [])
		for i in items.size():
			index[i] = Game.hero.inventory.index_of(items[i])
		trade_changed.emit()
		var result := await Official.commit_trade(other, mine, theirs, trade_id, index)
		if result.has("error"):
			# nothing changed hands; the other player is told (unless they cancelled first)
			if in_trade() and String(trade.get("trade_id", "")) == trade_id:
				trade_cancel(String(result.error))
			else:
				Events.notify.emit(String(result.error), &"info")
			return
		var confirmed := HeroData.from_dict(result.save.hero)
		Game.hero.inventory.cells = confirmed.inventory.cells
		Game.hero.inventory.gold = confirmed.inventory.gold
		Game.hero.inventory.changed.emit()
		Events.notify.emit("Trade complete with %s, saved on the official server: you gave %s and received %s." % [who, TradeRules.describe(mine), TradeRules.describe(theirs)], &"loot")
		Audio.play_ui(&"level_up")
		if in_trade() and String(trade.get("trade_id", "")) == trade_id:
			trade_reset("")
		Game.save_now()
		return
	var err := TradeRules.swap(Game.hero, mine, theirs)
	if err != "":
		trade_cancel(err)
		return
	Events.notify.emit("Trade complete with %s: you gave %s and received %s." % [who, TradeRules.describe(mine), TradeRules.describe(theirs)], &"loot")
	Audio.play_ui(&"level_up")
	trade_reset("")
	Game.save_now()

## End the trade from here and tell the other player.
func trade_cancel(why := "") -> void:
	if not in_trade():
		return
	var peer := int(trade.peer)
	if Official.active and trade.has("trade_id"):
		Official.abort_trade(String(trade.trade_id), String(trade.get("other_character", "")))
	if peers.has(peer) and is_active():
		_trade_cancelled.rpc_id(peer, "%s cancelled the trade." % String(peers.get(my_id(), {}).get("name", "The other hero")) if why == "" else why)
	trade_reset(why if why != "" else "You cancelled the trade.")

@rpc("any_peer", "reliable")
func _trade_cancelled(why: String) -> void:
	if not in_trade() or int(trade.peer) != multiplayer.get_remote_sender_id():
		return
	if Official.active and trade.has("trade_id"):
		# this side may already be waiting on the server: withdraw there too, so nobody waits out the expiry
		Official.abort_trade(String(trade.trade_id), String(trade.get("other_character", "")))
	trade_reset(why)

## Drop the trade state and close the window; `why` (if any) is shown as a notice.
func trade_reset(why := "") -> void:
	var had := in_trade()
	trade = {}
	if had:
		trade_changed.emit()
		if why != "":
			Events.notify.emit(why, &"info")

# ---- Ping markers (bh-011) ----------------------------------------------------------------------------------------

## Mark a spot for the whole party (offline it marks it just for you).
func ping(at: Vector3) -> void:
	var h := Game.hero
	var who := h.hero_name if h else "You"
	show_ping(at, who, player_color(my_id()) if is_active() else PLAYER_COLORS[0])
	if is_active():
		_remote_ping.rpc(String(Game.current_map_id), at, who)

@rpc("any_peer", "unreliable")
func _remote_ping(map: String, at: Vector3, who: String) -> void:
	if map != String(Game.current_map_id) or FX.world == null or Game.travelling:
		return
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from) or not at.is_finite() or not NetGuard.allow(from, "ping", 1.0, 3.0):
		return
	who = ChatText.clean(who).left(18)
	show_ping(at, who, player_color(from))
	Events.notify.emit("%s marked a spot." % who, &"info")

func show_ping(at: Vector3, who: String, col: Color) -> void:
	if FX.world == null or not is_instance_valid(FX.world):
		return
	var n := PingMarker.new()
	n.setup(who, col, PING_LIFE)
	FX.world.add_child(n)
	n.global_position = at
	Audio.play_at(&"ui_hover", at, 4.0)

# ---- Host: send a player home (bh-011) ----------------------------------------------------------------------------

func kick(id: int) -> void:
	if not is_host() or id == 1 or not peers.has(id):
		return
	var who: String = peers[id].get("name", "A hero")
	_rejected.rpc_id(id, "The host sent you back to your own world.")
	get_tree().create_timer(0.4).timeout.connect(func() -> void:
		if _peer:
			_peer.disconnect_peer(id))
	_chat_system("%s was sent home by the host." % who, true)

# ---- Guilds, whispers and Showcase (bh-027) ----------------------------------------------------------------------------
##   Profiles   every player's profile carries their guild (GuildRules.guild_key, name, colour, motto, master, level,
##              members, banner hash). A guild seen on another player is imported into this hero's Guild House.
##   Banners    an uploaded banner (a JPEG of up to 400 KB) travels once per player and per change, reliably.
##   Invites    a Guildmaster invites a player (their menu: Invite to Guild); on Accept the player joins as a Sworn Hero
##              and receives the guild's snapshot (name, motto, info, passives, banner). Changes the Guildmaster makes
##              reach connected members; a kick or a leave is sent to the other side.
##   Whisper    a private line to one player (the chat's /w <name> <text>).
##   Showcase   ask a player to show their equipped gear: on Yes both see both heroes' gear side by side, and their guilds.

var guild_banners := {}              # guild key -> JPEG bytes received from other players
## bh-030: other players' profile pictures (peer -> JPEG bytes) and the version of mine each peer already has.
var profile_pictures := {}
var _pic_sent := {}
var _banner_sent := {}               # peer -> banner hash already sent to them
var _sync_sent := {}                 # peer -> hash of the guild snapshot last sent to them (Guildmaster)
var _guild_asked := {}               # an invitation waiting for this player's answer {peer, snap}
var _showcase_t := 0.0

static func guild_profile(h: HeroData) -> Dictionary:
	if h == null or h.guild == &"":
		return {}
	var g := GuildRegistry.info(h, h.guild)
	if g.is_empty():
		return {}
	var bytes: Variant = h.guild_banner if h.guild == GuildRegistry.OWN else (h.remote_guild.get("banner", PackedByteArray()) if h.guild == GuildRegistry.REMOTE else PackedByteArray())
	return {"key": GuildRules.guild_key(h), "name": GuildRules.display_name(h), "color": (g.color as Color).to_html(false),
		"motto": String(g.get("motto", "")), "master": String(g.get("master", "")), "level": int(g.get("level", 1)),
		"members": int(g.get("members", 1)), "info": String(g.get("info", "")), "style": g.get("style", {}), "kind": String(g.kind),
		"bsig": hash(bytes) if bytes is PackedByteArray and not (bytes as PackedByteArray).is_empty() else 0,
		"passives": (g.get("passives", {}) as Dictionary).duplicate()}

## Another player by hero name (never this machine's own hero, even when two heroes share a name).
func peer_by_name(pname: String) -> int:
	for id in peers:
		if int(id) != my_id() and GuildRules.clean_alias(String(peers[id].get("name", ""))) == GuildRules.clean_alias(pname):
			return int(id)
	return 0

func _on_my_guild_changed() -> void:
	if not is_active() or connecting:
		return
	update_profile()
	_send_banner_all()
	# a Guildmaster's changes reach the members who are here
	var h := Game.hero
	if OwnGuild.is_master(h):
		for id in peers:
			if id != my_id() and OwnGuild.has_player_member(h, String(peers[id].get("name", ""))):
				_sync_member(int(id))

## Send a member the guild as it is now, once per change (profiles arrive often; a sync is only sent when it differs).
func _sync_member(id: int) -> void:
	var snap := OwnGuild.snapshot(Game.hero, false)
	var sig := hash(snap)
	if int(_sync_sent.get(id, 0)) == sig:
		return
	_sync_sent[id] = sig
	_guild_sync.rpc_id(id, snap)

## bh-030: send my profile picture to every player who does not have this version yet (an empty picture is sent too,
## once, so a removed picture disappears for everyone).
func send_profile_picture_all() -> void:
	var h := Game.hero
	if h == null or not is_active() or connecting:
		return
	# bh-031: without a profile picture the hero shares their ID picture (an ID shot of their own model)
	var pic := ProfilePicture.shown_bytes(h)
	var sig := hash(pic) if not pic.is_empty() else 1
	for id in peers:
		if id == my_id() or int(_pic_sent.get(id, 0)) == sig:
			continue
		if sig == 1 and not _pic_sent.has(id):
			_pic_sent[id] = sig          # nothing to clear on a player who never had one
			continue
		_pic_sent[id] = sig
		_profile_picture.rpc_id(id, pic)

@rpc("any_peer", "reliable")
func _profile_picture(bytes: PackedByteArray) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from):
		return
	if bytes.is_empty():
		profile_pictures.erase(from)
	elif ProfilePicture.valid(bytes):
		profile_pictures[from] = bytes
	else:
		return
	Events.profile_picture_changed.emit(from)

## Send my guild's banner picture to everyone who has not got this version of it.
func _send_banner_all() -> void:
	var h := Game.hero
	if h == null or not is_active():
		return
	var prof := guild_profile(h)
	var bytes: PackedByteArray = h.guild_banner if h.guild == GuildRegistry.OWN else PackedByteArray()
	if prof.is_empty() or bytes.is_empty():
		return
	var sig := hash(bytes)
	for id in peers:
		if id == my_id() or int(_banner_sent.get(id, 0)) == sig:
			continue
		_banner_sent[id] = sig
		_guild_banner.rpc_id(id, String(prof.key), bytes)

@rpc("any_peer", "reliable")
func _guild_banner(key: String, bytes: PackedByteArray) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from) or bytes.size() > GuildRules.BANNER_MAX_BYTES:
		return
	var probe := Image.new()
	if probe.load_jpg_from_buffer(bytes) != OK:
		return
	guild_banners[key] = bytes
	_import_peer_guild(from)
	Events.guild_changed.emit()

## Remember a fellow player's guild in this hero's world (the Guild House hangs their banner).
func _import_peer_guild(id: int) -> void:
	var h := Game.hero
	var g: Dictionary = peers.get(id, {}).get("guild", {})
	if h == null or g.is_empty() or String(g.get("key", "")) == "" or String(g.get("key", "")).begins_with("canon/"):
		return
	if String(g.key) == GuildRules.guild_key(h):
		return
	var snap := g.duplicate()
	snap["banner"] = guild_banners.get(String(g.key), PackedByteArray())
	GuildRegistry.import_remote(h, snap)

func _on_peers_for_guilds() -> void:
	if not is_active() or connecting:
		return
	_send_banner_all()
	send_profile_picture_all()
	var h := Game.hero
	for id in peers:
		if id == my_id():
			continue
		_import_peer_guild(int(id))
		# a player who still flies my banner but was sent away while they were gone
		var g: Dictionary = peers[id].get("guild", {})
		if h and OwnGuild.is_master(h) and String(g.get("kind", "")) == "remote" and String(g.get("master", "")) == GuildRules.clean_alias(h.hero_name) \
				and not OwnGuild.has_player_member(h, String(peers[id].get("name", ""))) and int(_sync_sent.get(id, 0)) != -1:
			_sync_sent[id] = -1
			_guild_kicked.rpc_id(id, GuildRules.clean_alias(h.hero_name))
		# a fellow member whose Guildmaster is here: bring their copy of the guild up to date
		if h and OwnGuild.is_master(h) and OwnGuild.has_player_member(h, String(peers[id].get("name", ""))):
			_sync_member(int(id))

# ---- whispers ----------------------------------------------------------------------------------------------------

func whisper(peer: int, text: String) -> String:
	var clean := ChatText.clean(text)
	if not is_active() or not peers.has(peer) or peer == my_id():
		return "Nobody by that name is here."
	if clean.is_empty():
		return "Say something."
	_whisper.rpc_id(peer, clean)
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.chat.add_line("[To %s] %s" % [peers[peer].get("name", "Hero"), clean], Color(0.85, 0.6, 1.0))
	return ""

@rpc("any_peer", "reliable")
func _whisper(text: String) -> void:
	var from := multiplayer.get_remote_sender_id()
	var clean := ChatText.clean(text)
	if not peers.has(from) or clean.is_empty():
		return
	if Game.ui_root and is_instance_valid(Game.ui_root):
		Game.ui_root.chat.add_line("[From %s] %s" % [peers[from].get("name", "Hero"), clean], Color(0.85, 0.6, 1.0))
	Audio.play_ui(&"ui_hover", -4.0)

# ---- guild invitations ------------------------------------------------------------------------------------------

func guild_invite_error(peer: int) -> String:
	var h := Game.hero
	if not is_active() or not peers.has(peer) or peer == my_id():
		return "Nobody by that name is here."
	if not OwnGuild.is_master(h):
		return "Found a guild of your own first (Guild window, %s)." % Settings.binding_text(&"guild")
	var pname := String(peers[peer].get("name", ""))
	if OwnGuild.has_player_member(h, pname) or String(peers[peer].get("guild", {}).get("key", "")) == OwnGuild.key(h):
		return "%s is already in %s." % [pname, h.own_guild.name]
	if OwnGuild.free_slots(h) <= 0:
		return "%s is full. Expand the guild or dismiss a member." % h.own_guild.name
	return ""

func guild_invite(peer: int) -> String:
	var err := guild_invite_error(peer)
	if err != "":
		Events.notify.emit(err, &"error")
		return err
	_guild_invite_ask.rpc_id(peer, OwnGuild.snapshot(Game.hero, false))
	Events.notify.emit("Guild invitation sent to %s." % peers[peer].get("name", "them"), &"info")
	return ""

@rpc("any_peer", "reliable")
func _guild_invite_ask(snap: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	var h := Game.hero
	var g := GuildRegistry.clean_remote(snap)
	if not peers.has(from) or h == null or g.is_empty() or Game.ui_root == null or not is_instance_valid(Game.ui_root):
		return
	if OwnGuild.is_master(h):
		_guild_invite_reply.rpc_id(from, false, {"why": "%s leads a guild of their own." % h.hero_name})
		return
	_guild_asked = {"peer": from, "snap": g}
	var now := "" if h.guild == &"" else "\nYou will leave %s (your Class %s tier stays yours)." % [GuildRules.display_name(h), DataGuilds.letter(h.tier)]
	Game.ui_root.ask("Guild Invitation", "%s invites you to join %s (guild level %d, %d members).\n“%s”%s" % [g.master, g.name, g.level, g.members,
			g.motto, now], func() -> void: answer_guild_invite(true), "Join %s" % g.name)
	get_tree().create_timer(40.0).timeout.connect(func() -> void:
		if int(_guild_asked.get("peer", 0)) == from:
			answer_guild_invite(false))

func answer_guild_invite(yes: bool) -> void:
	var from := int(_guild_asked.get("peer", 0))
	_guild_asked = {}
	var h := Game.hero
	if from == 0 or not peers.has(from) or h == null:
		return
	_guild_invite_reply.rpc_id(from, yes, {"name": h.hero_name, "cls": String(h.cls.id), "level": h.progress.level, "why": "%s said no." % h.hero_name})

@rpc("any_peer", "reliable")
func _guild_invite_reply(yes: bool, who: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	var h := Game.hero
	if not peers.has(from) or h == null:
		return
	if not yes:
		Events.notify.emit(String(who.get("why", "The invitation was declined.")), &"info")
		return
	var pname := String(peers[from].get("name", who.get("name", "")))
	var err := OwnGuild.add_player_member(h, pname, String(who.get("cls", "knight")), int(who.get("level", 1)))
	if err != "":
		Events.notify.emit(err, &"error")
		return
	_guild_welcome.rpc_id(from, OwnGuild.snapshot(h, true))
	_chat_system("%s joined %s!" % [pname, h.own_guild.name])

@rpc("any_peer", "reliable")
func _guild_welcome(snap: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	var h := Game.hero
	var g := GuildRegistry.clean_remote(snap)
	if not peers.has(from) or h == null or g.is_empty() or OwnGuild.is_master(h):
		return
	var first := h.guild == &""
	h.guild = GuildRegistry.REMOTE
	h.remote_guild = g
	h.guild_alias = ""
	if h.tier < 1:
		h.set_tier(1)
	h.stats_dirty.emit()
	Events.guild_joined.emit(GuildRegistry.REMOTE, first)
	Events.guild_changed.emit()
	Events.notify.emit("You joined %s, led by %s!" % [g.name, g.master], &"discovery")
	Game.save_now()

@rpc("any_peer", "reliable")
func _guild_sync(snap: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	var h := Game.hero
	var g := GuildRegistry.clean_remote(snap)
	if not peers.has(from) or h == null or g.is_empty() or h.guild != GuildRegistry.REMOTE:
		return
	if String(h.remote_guild.get("master", "")) != String(g.master):
		return
	if (g.banner as PackedByteArray).is_empty():
		g.banner = h.remote_guild.get("banner", PackedByteArray())
	if GuildRegistry._same_snapshot(h.remote_guild, g):
		return
	h.remote_guild = g
	h.stats_dirty.emit()
	Events.guild_changed.emit()

## The Guildmaster dismissed a fellow player (OwnGuild.kick): tell them if they are here.
func guild_kick_player(pname: String) -> void:
	if not is_active():
		return
	var id := peer_by_name(pname)
	if id != 0 and Game.hero:
		_guild_kicked.rpc_id(id, GuildRules.clean_alias(Game.hero.hero_name))

@rpc("any_peer", "reliable")
func _guild_kicked(master: String) -> void:
	var h := Game.hero
	if h == null or h.guild != GuildRegistry.REMOTE or String(h.remote_guild.get("master", "")) != master:
		return
	var was := String(h.remote_guild.get("name", "the guild"))
	h.guild = &""
	h.remote_guild = {}
	h.stats_dirty.emit()
	Events.guild_changed.emit()
	Events.notify.emit("%s dismissed you from %s." % [master, was], &"error")

## This player left a fellow hero's guild (GuildRules.leave): tell the Guildmaster if they are here.
func guild_left(master: String) -> void:
	if not is_active():
		return
	var id := peer_by_name(master)
	if id != 0:
		_guild_member_left.rpc_id(id)

@rpc("any_peer", "reliable")
func _guild_member_left() -> void:
	var from := multiplayer.get_remote_sender_id()
	var h := Game.hero
	if not peers.has(from) or not OwnGuild.is_master(h):
		return
	var pname := String(peers[from].get("name", ""))
	for m in OwnGuild.members(h):
		if String(m.kind) == "player" and String(m.name) == pname:
			(h.own_guild.members as Array).erase(m)
			Events.notify.emit("%s left %s." % [pname, h.own_guild.name], &"info")
			Events.guild_changed.emit()
			return

# ---- Showcase ---------------------------------------------------------------------------------------------------

## What a Showcase shows of this hero: name, class, level, look, equipped gear, guild (no stats).
static func showcase_pack(h: HeroData) -> Dictionary:
	if h == null:
		return {}
	var g := guild_profile(h)
	if not g.is_empty():
		var bytes = h.remote_guild.get("banner", PackedByteArray()) if h.guild == GuildRegistry.REMOTE else h.guild_banner
		g["banner"] = bytes if bytes is PackedByteArray else PackedByteArray()
		g["id"] = String(h.guild)
	return {"name": h.hero_name, "cls": String(h.cls.id), "path": profile_path(h), "level": h.progress.level, "tier": h.tier, "look": h.look.duplicate(true),
		"equipment": h.equipment.to_dict(), "guild": g}

func showcase_error(peer: int) -> String:
	if not is_active() or not peers.has(peer) or peer == my_id():
		return "Nobody by that name is here."
	if Time.get_ticks_msec() * 0.001 - _showcase_t < 3.0:
		return "Wait a moment before asking again."
	return ""

func request_showcase(peer: int) -> String:
	var err := showcase_error(peer)
	if err != "":
		Events.notify.emit(err, &"error")
		return err
	_showcase_t = Time.get_ticks_msec() * 0.001
	_showcase_ask.rpc_id(peer, showcase_pack(Game.hero))
	Events.notify.emit("Showcase request sent to %s." % peers[peer].get("name", "them"), &"info")
	return ""

@rpc("any_peer", "reliable")
func _showcase_ask(theirs: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from) or Game.hero == null or Game.ui_root == null or not is_instance_valid(Game.ui_root):
		return
	var who := String(peers[from].get("name", "A hero"))
	Game.ui_root.ask("Showcase", "%s would like to see your equipped gear and weapon (only what you wear - no stats).\nShow them? You will see theirs too." % who,
		func() -> void:
			if not peers.has(from):
				return
			_showcase_reply.rpc_id(from, true, showcase_pack(Game.hero))
			Game.ui_root.open_showcase(showcase_pack(Game.hero), theirs), "Show My Gear")

@rpc("any_peer", "reliable")
func _showcase_reply(yes: bool, theirs: Dictionary) -> void:
	var from := multiplayer.get_remote_sender_id()
	if not peers.has(from) or Game.ui_root == null or not is_instance_valid(Game.ui_root):
		return
	if not yes:
		Events.notify.emit("%s would rather not show their gear." % peers[from].get("name", "They"), &"info")
		return
	Game.ui_root.open_showcase(showcase_pack(Game.hero), theirs)
