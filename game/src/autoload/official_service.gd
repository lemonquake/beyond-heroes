extends Node
## Official accounts and durable server saves. Credentials/tokens are kept in memory only.
## Character snapshots use an exclusive lease, revision and retry identity; custom saves are separate.

signal changed
signal save_finished(ok: bool)
signal connection_lost(reason: String)

const CONFIG := "user://official_endpoint.cfg"
const SAVE_INTERVAL := 5.0
var url := "https://127.0.0.1:8443"
var certificate_path := "res://server/official_ca.crt"
var userid := ""
var token := ""
var characters: Array = []
var health := {}
var character_id := ""
var lease := ""
var ticket := ""
var revision := 0
var active := false
var connected := false
var saving := false
var save_state := ""
var last_saved_at := 0.0
var last_error := ""
var _pending := {}
var _retry := {}
var _timer := 0.0
var _retry_at := 0.0
var _endpoint_epoch := 0
var _blocked := false
var _flushing := false
var _fatal := false
var _transacting := false
var _confirmed_save := {}

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for path in ["res://server/official.cfg", CONFIG]:
		var cfg := ConfigFile.new()
		if cfg.load(path) == OK:
			url = String(cfg.get_value("server", "url", url))
			certificate_path = String(cfg.get_value("server", "certificate", certificate_path))
	Events.xp_gained.connect(func(_xp: int) -> void: _queue_current())
	Events.player_leveled.connect(func(_level: int, _gained: int) -> void: _queue_current())

func configure(address: String, certificate: String) -> String:
	if active:
		return "Return to the main menu before changing servers."
	address = address.strip_edges().trim_suffix("/")
	if not valid_endpoint(address):
		return "Use an HTTPS server address, for example https://192.168.1.20:8443."
	url = address
	certificate_path = certificate.strip_edges()
	_endpoint_epoch += 1
	token = ""
	userid = ""
	characters.clear()
	health.clear()
	var cfg := ConfigFile.new()
	cfg.set_value("server", "url", url)
	cfg.set_value("server", "certificate", certificate_path)
	cfg.save(CONFIG)
	changed.emit()
	return ""

static func valid_endpoint(address: String) -> bool:
	if not address.begins_with("https://") or address.length() > 256:
		return false
	var host := address.substr(8)
	return host != "" and not host.contains("/") and not host.contains("@") and not host.contains("?") and not host.contains("#") and not host.contains(" ") and not host.contains("\n") and not host.contains("\r")

## Probes only (bh-041): extra seconds before every request, to play a distant player (a friend over a VPN) on one PC.
var probe_latency := 0.0

func request(path: String, data := {}, method := HTTPClient.METHOD_POST, authorized := true, body := "") -> Dictionary:
	if probe_latency > 0.0:
		await get_tree().create_timer(probe_latency, true).timeout
	if not valid_endpoint(url):
		return {"error": "Configure a valid HTTPS official server address.", "code": "invalid_endpoint"}
	var epoch := _endpoint_epoch
	var http := HTTPRequest.new()
	http.timeout = 20.0
	http.body_size_limit = 3 * 1024 * 1024
	http.max_redirects = 0
	http.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(http)
	if certificate_path != "":
		var ca := X509Certificate.new()
		if ca.load(certificate_path) != OK:
			http.queue_free()
			return {"error": "The server certificate is missing. Use the game build supplied by the server owner, or choose its public certificate.", "code": "certificate_missing"}
		http.set_tls_options(TLSOptions.client(ca))
	var headers := PackedStringArray(["Content-Type: application/json"])
	if authorized and token != "":
		headers.append("Authorization: Bearer " + token)
	if body == "" and method != HTTPClient.METHOD_GET:
		body = JSON.stringify(data)
	var err := http.request(url + path, headers, method, "" if method == HTTPClient.METHOD_GET else body)
	if err != OK:
		http.queue_free()
		return {"error": "Could not start the server connection.", "code": "connection_failed"}
	var result: Array = await http.request_completed
	http.queue_free()
	if epoch != _endpoint_epoch:
		return {"error": "Server selection changed.", "code": "cancelled"}
	if int(result[0]) != HTTPRequest.RESULT_SUCCESS:
		return {"error": describe_failure(int(result[0]), url, certificate_path != ""), "code": "connection_failed"}
	var parsed = JSON.parse_string((result[3] as PackedByteArray).get_string_from_utf8())
	if not parsed is Dictionary:
		return {"error": "The server returned an unreadable response.", "code": "invalid_response"}
	if int(result[1]) != 200 and not parsed.has("error"):
		parsed = {"error": "The server could not complete the request.", "code": "server_error"}
	return parsed

## What went wrong with a connection, in words a player can act on. `result` is an HTTPRequest.Result.
static func describe_failure(result: int, address: String, has_certificate_file: bool) -> String:
	var host := address.trim_prefix("https://").get_slice("/", 0)
	match result:
		HTTPRequest.RESULT_CANT_RESOLVE:
			return "The server name %s could not be found. Check the address for typing mistakes and that this device is online." % host
		HTTPRequest.RESULT_CANT_CONNECT, HTTPRequest.RESULT_CONNECTION_ERROR:
			return "Could not connect to %s. The server may be turned off, or a firewall or network may be blocking the connection. Try again in a minute, or ask the server owner if it is running." % host
		HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:
			if has_certificate_file:
				return "The secure connection to %s was refused: its certificate does not match the file chosen in Server Settings. Ask the server owner for their current certificate file." % host
			return "The secure connection to %s was refused. If the server owner gave you a certificate file, add it in Server Settings under Advanced. Otherwise check the address." % host
		HTTPRequest.RESULT_TIMEOUT, HTTPRequest.RESULT_NO_RESPONSE:
			return "%s did not answer in time. Check this device's internet connection, then try again." % host
		_:
			return "The connection to %s failed (code %d). Check the address and your internet connection, then try again." % [host, result]

## Plain explanation when the server's game version is not this game's version (server_protocol is what /health reported).
static func describe_version_mismatch(server_protocol: int, game_protocol: int, build := "") -> String:
	var tail := " (server %s)" % build if build != "" else ""
	if server_protocol > game_protocol:
		return "Your game is older than this server%s. Update the game, then try again." % tail
	return "This server is running an older version of the game%s. Ask the server owner to update it. You can keep playing offline meanwhile." % tail

func check_server() -> Dictionary:
	var result := await request("/health", {}, HTTPClient.METHOD_GET, false)
	if not result.has("error"):
		if int(result.get("protocol", -1)) != Net.PROTOCOL:
			result = {"error": describe_version_mismatch(int(result.get("protocol", -1)), Net.PROTOCOL, String(result.get("version", ""))), "code": "version_mismatch",
				"server_protocol": int(result.get("protocol", -1))}
		else:
			health = result
	changed.emit()
	return result

func authenticate(action: String, user: String, password: String, recovery := "") -> Dictionary:
	var result := await request("/auth/" + action, {"userid": user.strip_edges(), "password": password, "recovery_code": recovery}, HTTPClient.METHOD_POST, false)
	if not result.has("error"):
		token = String(result.get("token", ""))
		userid = String(result.get("userid", ""))
		characters.clear()
		await refresh_characters()
	changed.emit()
	return result

func refresh_characters() -> Dictionary:
	var result := await request("/characters/list")
	if not result.has("error"):
		characters = result.get("characters", [])
	changed.emit()
	return result

func logout() -> void:
	if active:
		return
	if token != "":
		await request("/account/logout")
	token = ""
	userid = ""
	characters.clear()
	changed.emit()

func slot_summary(slot: int) -> Dictionary:
	for character: Dictionary in characters:
		if int(character.get("slot", -1)) == slot:
			return character
	return {}

func add_character(hero: HeroData, slot: int, source := "") -> Dictionary:
	if hero == null:
		return {"error": "The local character could not be read."}
	var result := await request("/characters/create" if source == "" else "/characters/import", {
		"slot": slot, "save": {"version": SaveSystem.CURRENT_VERSION, "hero": hero.to_dict()}, "source": source})
	if not result.has("error"):
		await refresh_characters()
	return result

func begin_character(id: String) -> Dictionary:
	if active:
		return {"error": "A character is already active."}
	var result := await request("/characters/play", {"character": id})
	if result.has("error"):
		return result
	var address := url.substr(8)
	result["game_host"] = address.get_slice("]", 0).substr(1) if address.begins_with("[") else address.get_slice(":", 0)
	# Account and game services run on the same PC. Use the LAN/VPN/public route this client selected.
	character_id = id
	lease = String(result.get("lease", ""))
	ticket = String(result.get("ticket", ""))
	revision = int(result.get("revision", 0))
	_confirmed_save = result.get("save", {}).duplicate(true)
	active = true
	_blocked = false
	_fatal = false
	connected = false
	last_error = ""
	_retry.clear()
	_pending.clear()
	save_state = "Connecting to the official game server…"
	SaveSystem.scope = "official"
	changed.emit()
	return result

func game_connected() -> void:
	connected = true
	_blocked = false
	_timer = 0.0
	save_state = "Official character · saved on the server"
	_queue_current()
	changed.emit()

func game_disconnected(reason: String) -> void:
	if not active or _blocked:
		return
	_blocked = true
	connected = false
	Game.ui_blocking = true
	get_tree().paused = true
	save_state = "Disconnected · gameplay paused"
	last_error = reason
	_queue_current()
	connection_lost.emit(reason)
	changed.emit()

func _queue_current() -> void:
	if active and Game.hero and Game.in_session:
		TempoParty.sync_all()
		queue_save(Game.hero)

func queue_save(hero: HeroData) -> void:
	if not active or hero == null:
		return
	_pending = {"version": SaveSystem.CURRENT_VERSION, "hero": hero.to_dict()}
	if connected:
		save_state = "Saving to the official server…"
	changed.emit()
	if connected and not _transacting and not saving and Time.get_ticks_msec() * 0.001 >= _retry_at:
		_send_save()

func _send_save() -> void:
	if saving or _transacting or not active or (_pending.is_empty() and _retry.is_empty()):
		return
	saving = true
	if _retry.is_empty():
		_retry = {"character": character_id, "lease": lease, "revision": revision,
			"request_id": Crypto.new().generate_random_bytes(16).hex_encode(), "save": _pending}
		_pending = {}
	# bh-037: this runs every 5 s while playing online. The hero was gathered (to_dict) on an earlier frame; here, one frame
	# later, a binary snapshot, and the JSON is written on a worker thread. Encoding a big hero here cost ~25 ms a time.
	await get_tree().process_frame
	if _retry.is_empty() or not active:      # disconnected or reset meanwhile
		saving = false
		return
	var snap := var_to_bytes(_retry)
	var enc := {}
	var task := WorkerThreadPool.add_task(func() -> void:
		var copy = bytes_to_var(snap)
		enc["copy"] = copy
		enc["json"] = JSON.stringify(copy), false, "official save")
	while not WorkerThreadPool.is_task_completed(task):
		await get_tree().process_frame
	WorkerThreadPool.wait_for_task_completion(task)
	var result := await request("/characters/save", {}, HTTPClient.METHOD_POST, true, String(enc.get("json", "")))
	saving = false
	if result.has("error"):
		last_error = String(result.error)
		save_state = "Progress has not been confirmed by the server"
		_retry_at = Time.get_ticks_msec() * 0.001 + 3.0
		if result.get("code", "") in ["lease_expired", "revision_conflict", "unauthorized", "invalid_save", "invalid_data"]:
			_fatal = true
			game_disconnected(last_error)
		save_finished.emit(false)
	else:
		revision = int(result.get("revision", revision))
		_confirmed_save = (enc.get("copy", {}) as Dictionary).get("save", {})     # already a deep copy (decoded on the worker)
		last_saved_at = float(result.get("saved_at", 0.0))
		last_error = ""
		_retry = {}
		save_state = "Progress saved on the official server"
		save_finished.emit(true)
	changed.emit()

## Wait for a confirmed final save. No caller may claim success for a queued HTTP request.
func flush() -> bool:
	if not active:
		return true
	if _fatal:
		return false
	_flushing = true
	_queue_current()
	var deadline := Time.get_ticks_msec() + 20000
	while saving or not _pending.is_empty() or not _retry.is_empty():
		if Time.get_ticks_msec() >= deadline:
			_flushing = false
			return false
		if not saving:
			_send_save()
		await get_tree().create_timer(0.2, true).timeout
	_flushing = false
	return true

## Both authenticated owners approve matching offers. The service commits both inventories in one transaction.
## bh-041: a trade that ends without committing (either side withdrew, the offers did not match, it expired) changed
## nothing on the server, so it is an ordinary "the trade was cancelled" and play goes on. Only an outcome that stays
## unknown after asking the server again (the connection is gone) still sends the player back to the menu.
## `aborted` (Net) is checked between the steps: once the other player cancels, this side withdraws as well.
func commit_trade(other: String, mine: Dictionary, theirs: Dictionary, trade_id: String, mine_index := {}) -> Dictionary:
	if not connected or not await flush():
		return {"error": "Your progress could not be confirmed by the server before trading. Try the trade again in a moment."}
	if _trade_aborted.has(trade_id):
		return {"error": "The trade was cancelled.", "code": "trade_cancelled"}
	_transacting = true
	var trial := HeroData.from_dict(_confirmed_save.get("hero", {}))
	var outgoing := {"gold": int(mine.get("gold", 0)), "items": []}
	var mine_wire := TradeRules.to_wire(mine)
	var used := {}
	for i in mine_wire.items.size():
		var raw: Dictionary = mine_wire.items[i]
		var hit := -1
		# the bag cell the offered item sits in (the confirmed save is a copy of this very bag), then any equal item
		var at := int(mine_index.get(i, -1))
		if at >= 0 and at < trial.inventory.cells.size() and not used.has(at):
			var cand: ItemInstance = trial.inventory.cells[at]
			if cand and String(cand.base.id) == String(raw.get("base", "")) and cand.count == int(raw.get("count", 1)):
				hit = at
		if hit < 0:
			for index in trial.inventory.cells.size():
				var item: ItemInstance = trial.inventory.cells[index]
				if item and not used.has(index) and item.to_dict() == raw:
					hit = index
					break
		if hit < 0:
			_transacting = false
			return {"error": "Your bag changed while confirming the trade. Review the offers again."}
		outgoing.items.append(trial.inventory.cells[hit])
		used[hit] = true
	# what this side sends as "mine" must be exactly what the other side received as "theirs" (and the reverse): the wire
	# form this machine sent over the network, and the other player's offer exactly as it arrived
	mine_wire = mine.get("wire", TradeRules.to_wire(outgoing))
	var theirs_wire: Dictionary = theirs.get("wire", TradeRules.to_wire(theirs))
	var incoming := TradeRules.read_incoming(theirs_wire)
	var error := TradeRules.swap_error(trial, outgoing, incoming)
	if error != "":
		_transacting = false
		return {"error": error}
	var proposed: Dictionary = _confirmed_save.duplicate(true)
	var bag := trade_bag(proposed.hero.get("inventory", []), used.keys(), theirs_wire.get("items", []), trial.inventory.bag_capacity)
	if bag.is_empty():
		# no room without merging stacks: let the rules place them (merging into stacks already in the bag)
		TradeRules.swap(trial, outgoing, incoming)
		bag = trial.inventory.to_array()
	proposed.hero["inventory"] = bag
	proposed.hero["gold"] = int(proposed.hero.get("gold", 0)) - int(mine_wire.get("gold", 0)) + int(theirs_wire.get("gold", 0))
	var body := {"character": character_id, "lease": lease, "trade_id": trade_id,
		"other": other, "revision": revision, "mine": mine_wire, "theirs": theirs_wire, "save": proposed}
	var result := await request("/characters/trade_prepare", body)
	var deadline := Time.get_ticks_msec() + 50000
	var asked := {"character": character_id, "lease": lease, "trade_id": trade_id, "other": other}
	while Time.get_ticks_msec() < deadline:
		if result.get("state", "") in ["committed", "cancelled"] or result.get("code", "") in ["trade_cancelled", "revision_conflict", "lease_expired"]:
			break
		if _trade_aborted.has(trade_id) or (result.has("error") and result.get("code", "") != "connection_failed"):
			# withdraw: this side's approval was refused or the other player left the table
			result = await request("/characters/trade_cancel", asked)
			continue
		await get_tree().create_timer(0.4, true).timeout
		result = await request("/characters/trade_status", asked)
	if not result.get("state", "") in ["committed", "cancelled"] and result.get("code", "") != "trade_cancelled":
		# out of time or out of touch: one last withdrawal, which also reports a commit that did happen
		for attempt in 3:
			var last := await request("/characters/trade_cancel", asked)
			if last.get("state", "") in ["committed", "cancelled"]:
				result = last
				break
			await get_tree().create_timer(1.0, true).timeout
	_transacting = false
	_trade_aborted.erase(trade_id)
	if result.get("state", "") == "committed" and result.get("save", null) is Dictionary:
		revision = int(result.revision)
		_confirmed_save = result.save.duplicate(true)
		_pending = {}
		return result
	if result.get("state", "") == "cancelled" or result.get("code", "") == "trade_cancelled":
		return {"error": String(result.get("error", "The trade was cancelled. Nothing changed hands.")), "code": "trade_cancelled"}
	if result.get("code", "") == "revision_conflict" or result.get("code", "") == "lease_expired":
		_fatal = true
		game_disconnected(String(result.get("error", "Your character changed on the server.")) + " Return to the menu and load the server's saved character.")
		return {"error": "The trade was not confirmed. Reload your character's server save."}
	_fatal = true
	game_disconnected("The trade could not be confirmed because the server stopped answering. Return to the menu and load the server's saved character before playing again. " + String(result.get("error", "")))
	return {"error": "The trade was not confirmed. Reload your character's server save."}

## bh-041: the bag after a trade, written straight from the saved one: the offered cells emptied and the arriving items
## (exactly as they arrived, minus the sender's locks and marks) placed in free bag cells. Nothing is decoded and encoded
## again, so the server sees the very same item records on both sides. [] when they do not fit without merging stacks.
static func trade_bag(saved: Array, leaving: Array, arriving: Array, bag_capacity: int) -> Array:
	var bag := saved.duplicate(true)
	for i in leaving:
		if int(i) < bag.size():
			bag[int(i)] = null
	for raw in arriving:
		if not raw is Dictionary:
			continue
		var item: Dictionary = (raw as Dictionary).duplicate(true)
		for flag in ["locked", "favorite", "junk"]:
			item.erase(flag)
		var placed := false
		for i in mini(bag_capacity, bag.size()):
			if bag[i] == null:
				bag[i] = item
				placed = true
				break
		if not placed:
			return []
	return bag

## bh-041: the other player cancelled (or this side gave up) while `trade_id` was being confirmed: stop waiting for it and
## withdraw it on the server, so neither player waits out the expiry.
var _trade_aborted := {}

func abort_trade(trade_id: String, other := "") -> void:
	if trade_id == "" or not active:
		return
	_trade_aborted[trade_id] = true
	request("/characters/trade_cancel", {"character": character_id, "lease": lease, "trade_id": trade_id, "other": other})

func release_character() -> void:
	if active:
		await request("/characters/release", {"character": character_id, "lease": lease})
	active = false
	connected = false
	character_id = ""
	lease = ""
	ticket = ""
	_pending.clear()
	_retry.clear()
	save_state = ""
	SaveSystem.scope = "legacy"
	changed.emit()

func _process(delta: float) -> void:
	if not active:
		return
	if not connected and Game.in_session:
		get_tree().paused = true
	_timer += delta
	if connected and not _flushing and not _transacting and Game.in_session and not Game.travelling and _timer >= SAVE_INTERVAL:
		_timer = 0.0
		_queue_current()
	if not saving and not _fatal and not _retry.is_empty() and Time.get_ticks_msec() * 0.001 >= _retry_at:
		_send_save()
