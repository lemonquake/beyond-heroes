extends Node
## Two-machine probe for bh-015's independent exploring and party summons. Run two copies on one PC:
##   godot --path game --resolution 1280x720 res://tests/tools/net_probe_explore.tscn -- --role=host --class=knight --slot=94 --map=ruined_forest --out=<dir>
##   godot --path game --resolution 1280x720 res://tests/tools/net_probe_explore.tscn -- --role=join --class=ranger --slot=93 --map=sanctuary --out=<dir>
## Checks (EXPLORE[role] ok/FAIL lines):
##   the client arrives at the host's side once, sharing the host's monsters; it then travels on its own (no request)
##   and gets its own monsters there; both see where the other is (Net.status, party frames, minimap, world map); the
##   host summons, the client says Go and lands beside the host; the host leaves: the client stays and its map fills
##   with its own monsters; the host comes back and shares the client's monsters (bh-032: the first explorer stays in
##   charge of a map); a second summons answered Stay keeps the client put.

var args := {}
var role := "host"
var out := ""
var fails: Array = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/explore")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("EXPLORE[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

func _log(s: String) -> void:
	print("EXPLORE[%s] %s" % [role, s])

func _wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [role, label]))

func _settled(map: StringName, limit := 60.0) -> bool:
	var t := 0.0
	while t < limit:
		if Game.current_map_id == map and not Game.travelling and not Net.following:
			return true
		await _wait(0.1)
		t += 0.1
	return false

static func _local_monsters() -> int:
	var n := 0
	for e in Game.player.get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and not e.net_replica and Game.current_map.is_ancestor_of(e):
			n += 1
	return n

static func _replicas() -> int:
	var n := 0
	for e in Game.player.get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.net_replica:
			n += 1
	return n

func _run() -> void:
	for i in 400:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await _wait(0.1)
	await _wait(1.0)
	Game.god_mode = true
	if role == "host":
		await _host()
	else:
		await _client()
	print("EXPLORE[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

func _client_id() -> int:
	for id in Net.peers:
		if int(id) != 1:
			return int(id)
	return 0

func _host() -> void:
	var err := Net.host_game()
	_check("hosted (%s)" % err, err == "")
	for i in 400:
		if Net.player_count() >= 2 and Net.avatars().size() > 0:
			break
		await _wait(0.1)
	_check("the client joined beside the host", Net.avatars().size() > 0)
	# wait until the client has gone off on its own
	var cid := 0
	var away := false
	for i in 600:
		cid = _client_id()
		if cid != 0 and String(Net.status.get(cid, {}).get("map", "")) == "westreach":
			away = true
			break
		await _wait(0.1)
	_check("the host knows the client went to Westreach by itself (%s)" % Net.status.get(cid, {}).get("map", "?"), away)
	_check("the host stayed in the Ruined Forest", Game.current_map_id == &"ruined_forest")
	await _wait(2.0)
	Game.ui_root.open(&"world_map")
	await _wait(1.5)
	await _shot("world_map_ally")
	Game.ui_root.close_all()
	await _shot("party_frames_away")
	# summon: the client says Go
	var asked := Net.summon_party()
	_check("Summon Party asked %d player(s)" % asked, asked == 1)
	var back := false
	for i in 600:
		var av := Net.avatar(cid)
		if av and av.global_position.distance_to((Game.player as Node3D).global_position) < 8.0:
			back = true
			break
		await _wait(0.1)
	_check("the summoned client arrived at the host's side", back)
	await _wait(2.0)
	await _shot("summoned_beside")
	# the host leaves for town; the client stays in the forest
	Game.travel(&"sanctuary", &"waypoint")
	await _settled(&"sanctuary")
	await _wait(8.0)
	_check("the client stayed in the forest while the host left (%s)" % Net.status.get(cid, {}).get("map", "?"),
		String(Net.status.get(cid, {}).get("map", "")) == "ruined_forest")
	# and back again
	Game.travel(&"ruined_forest", &"arrival")
	await _settled(&"ruined_forest")
	await _wait(10.0)
	# a second summons, which the client refuses: nothing moves
	for i in 300:
		if String(Net.status.get(cid, {}).get("map", "")) == "westreach":
			break
		await _wait(0.1)
	await _wait(1.0)
	_check("second summons asked the client", Net.summon_party() == 1)
	await _wait(6.0)
	_check("a client who says Stay stays in %s" % Net.status.get(cid, {}).get("map", "?"), String(Net.status.get(cid, {}).get("map", "")) == "westreach")
	await _wait(3.0)
	Net.leave()

func _client() -> void:
	await _wait(3.0)
	var err := Net.join_game(NetCodec.room_code("127.0.0.1", Net.PORT, Net.PORT))
	_check("join sent (%s)" % err, err == "")
	for i in 400:
		if Net.is_client() and not Net.connecting and not Net.following and Game.current_map_id == &"ruined_forest" and not Game.travelling:
			break
		await _wait(0.1)
	_check("arrived at the host's side in the Ruined Forest on joining", Game.current_map_id == &"ruined_forest")
	await _wait(4.0)
	_check("sharing the host's world: no monsters of its own (%d), %d replicas" % [_local_monsters(), _replicas()], _local_monsters() == 0 and Net._host_shared)
	await _shot("minimap_beside_host")
	# explore alone: no request, no waiting for the host
	Game.travel(&"westreach", &"start")
	var went := await _settled(&"westreach")
	_check("travelled to Westreach on its own", went)
	await _wait(3.0)
	_check("its own monsters in its own world (%d)" % _local_monsters(), _local_monsters() > 0 and not Net._host_shared)
	_check("knows the host is in the Ruined Forest", String(Net.status.get(1, {}).get("map", "")) == "ruined_forest")
	var hud: Hud = Game.ui_root.hud
	var sub: String = hud.party_frames._rows[1].sub.text if hud.party_frames._rows.has(1) else ""
	_check("the host's party frame says where they are: '%s'" % sub, sub.contains("Ruined Forest"))
	await _shot("party_frame_host_elsewhere")
	# the host summons: Go
	var asked := false
	for i in 300:
		if Game.ui_root.confirm.visible and Game.ui_root.confirm._title.text == "Summoned":
			asked = true
			break
		await _wait(0.1)
	_check("summoned: '%s'" % (Game.ui_root.confirm._text.text if asked else ""), asked)
	await _shot("summon_dialog")
	if asked:
		Game.ui_root.confirm._confirm()
	var there := await _settled(&"ruined_forest")
	_check("Go carried it to the host's map", there)
	await _wait(3.0)
	var hav := Net.avatar(1)
	var d := (Game.player as Node3D).global_position.distance_to(hav.global_position) if hav else -1.0
	_check("standing beside the host (%.1f m)" % d, hav != null and d < 8.0)
	_check("sharing again: no monsters of its own (%d)" % _local_monsters(), _local_monsters() == 0)
	# the host leaves: this map becomes the client's own
	var own := false
	for i in 400:
		if not Net._host_shared and _local_monsters() > 0:
			own = true
			break
		await _wait(0.1)
	_check("the host left: the forest filled with its own monsters (%d)" % _local_monsters(), own)
	_check("and it did not have to move (%s)" % Game.current_map_id, Game.current_map_id == &"ruined_forest")
	await _shot("host_left_minimap")
	# the host comes back. Since bh-032 a map keeps its first explorer in charge: this machine still runs the forest
	# and the host shares its monsters (until bh-032 the host's monsters replaced this machine's own)
	var shared := false
	for i in 400:
		if Net.avatar(1) != null and Net.status.get(1, {}).get("map", "") == "ruined_forest" and not Net._host_shared 				and _local_monsters() > 0 and Net.world_owner(&"ruined_forest") == Net.my_id():
			shared = true
			break
		await _wait(0.1)
	_check("the host came back: this machine keeps running the forest and the host shares it", shared)
	await _wait(3.0)
	var hav2 := Net.avatar(1)
	if hav2:
		(Game.player as Player).teleport_to(hav2.global_position + Vector3(22, 0, 14))
	await _wait(2.5)
	await _shot("minimap_host_on_rim")
	# off again; the next summons is answered Stay
	Game.travel(&"westreach", &"start")
	await _settled(&"westreach")
	var asked2 := false
	for i in 300:
		if Game.ui_root.confirm.visible and Game.ui_root.confirm._title.text == "Summoned":
			asked2 = true
			break
		await _wait(0.1)
	_check("summoned again", asked2)
	if asked2:
		Game.ui_root.confirm.cancel()
	await _wait(4.0)
	_check("Stay: still in Westreach", Game.current_map_id == &"westreach")
	for i in 200:
		if not Net.is_active():
			break
		await _wait(0.1)
	await _wait(2.0)
	_check("after the host closed the world, still in Westreach with its own monsters (%d)" % _local_monsters(),
		Game.current_map_id == &"westreach" and _local_monsters() > 0)
