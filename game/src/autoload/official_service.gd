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

func request(path: String, data := {}, method := HTTPClient.METHOD_POST, authorized := true) -> Dictionary:
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
	var err := http.request(url + path, headers, method, "" if method == HTTPClient.METHOD_GET else JSON.stringify(data))
	if err != OK:
		http.queue_free()
		return {"error": "Could not start the server connection.", "code": "connection_failed"}
	var result: Array = await http.request_completed
	http.queue_free()
	if epoch != _endpoint_epoch:
		return {"error": "Server selection changed.", "code": "cancelled"}
	if int(result[0]) != HTTPRequest.RESULT_SUCCESS:
		return {"error": "Could not reach the official server over a verified encrypted connection. Check its address, certificate and whether the server PC is running.", "code": "connection_failed"}
	var parsed = JSON.parse_string((result[3] as PackedByteArray).get_string_from_utf8())
	if not parsed is Dictionary:
		return {"error": "The server returned an unreadable response.", "code": "invalid_response"}
	if int(result[1]) != 200 and not parsed.has("error"):
		parsed = {"error": "The server could not complete the request.", "code": "server_error"}
	return parsed

func check_server() -> Dictionary:
	var result := await request("/health", {}, HTTPClient.METHOD_GET, false)
	if not result.has("error"):
		if int(result.get("protocol", -1)) != Net.PROTOCOL:
			result = {"error": "The official server and your game have different versions. Update both.", "code": "version_mismatch"}
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
	var result := await request("/characters/save", _retry)
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
		_confirmed_save = _retry.get("save", {}).duplicate(true)
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
func commit_trade(other: String, mine: Dictionary, theirs: Dictionary, trade_id: String) -> Dictionary:
	if not connected or not await flush():
		return {"error": "Confirm your server save before trading."}
	_transacting = true
	var trial := HeroData.from_dict(_confirmed_save.get("hero", {}))
	var outgoing := {"gold": int(mine.get("gold", 0)), "items": []}
	var mine_wire := TradeRules.to_wire(mine)
	var theirs_wire := TradeRules.to_wire(theirs)
	var used := {}
	for raw: Dictionary in mine_wire.items:
		var found := false
		for index in trial.inventory.cells.size():
			var item: ItemInstance = trial.inventory.cells[index]
			if item and not used.has(index) and item.to_dict() == raw:
				outgoing.items.append(item)
				used[index] = true
				found = true
				break
		if not found:
			_transacting = false
			return {"error": "Your bag changed while confirming the trade. Review the offers again."}
	var incoming := TradeRules.read_incoming(theirs_wire)
	var error := TradeRules.swap(trial, outgoing, incoming)
	if error != "":
		_transacting = false
		return {"error": error}
	var proposed: Dictionary = _confirmed_save.duplicate(true)
	proposed.hero["inventory"] = trial.inventory.to_array()
	proposed.hero["gold"] = trial.inventory.gold
	var body := {"character": character_id, "lease": lease, "trade_id": trade_id,
		"other": other, "revision": revision, "mine": mine_wire, "theirs": theirs_wire, "save": proposed}
	var result := await request("/characters/trade_prepare", body)
	var deadline := Time.get_ticks_msec() + 45000
	while not result.has("error") and result.get("state", "") == "pending" and Time.get_ticks_msec() < deadline:
		await get_tree().create_timer(0.4, true).timeout
		result = await request("/characters/trade_status", {"character": character_id, "lease": lease, "trade_id": trade_id})
	_transacting = false
	if result.has("error") or result.get("state", "") != "committed":
		_fatal = true
		game_disconnected("The trade could not be confirmed. Return to the menu and load the server's saved character before playing again. " + String(result.get("error", "The trade timed out.")))
		return {"error": "The trade was not confirmed. Reload your character's server save."}
	revision = int(result.revision)
	_confirmed_save = result.save.duplicate(true)
	_pending = {}
	return result

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
