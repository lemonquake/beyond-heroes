extends Node

const ROOM := "abcdef0123456789abcdef0123456789"
var role := "host"

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--role="):
			role = arg.substr(7)
	_run.call_deferred()

func _check(condition: bool, message: String) -> bool:
	if not condition:
		print("CUSTOM_PROBE FAIL ", role, " ", message)
		get_tree().quit(1)
	return condition

func _run() -> void:
	Official.url = "https://127.0.0.1:18443"
	Official.certificate_path = "res://server/official_ca.crt"
	SaveSystem.choose_custom_room(ROOM)
	Game.save_slot = 97
	Game.hero = Game.new_hero(&"knight" if role == "host" else &"mage", "CustomHost" if role == "host" else "CustomFriend")
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	await Game._begin_session(&"sanctuary", &"waypoint")
	Net.room_name = "Integration Custom Game"
	var error := Net.host_game(24691) if role == "host" else Net.join_game("127.0.0.1", 24691)
	if not _check(error == "", error):
		return
	for tick in 300:
		if Net.player_count() == 2 and not Net.connecting:
			break
		await get_tree().create_timer(0.1).timeout
	if not _check(Net.player_count() == 2, "two custom characters joined"):
		return
	if not _check(not Official.active and SaveSystem.scope == "custom", "custom character cannot become official"):
		return
	if role == "host":
		await Net._publish_custom()
		var result := await Official.request("/custom/list", {}, HTTPClient.METHOD_GET, false)
		var found := false
		for game: Dictionary in result.get("games", []):
			if game.get("room", "") == ROOM and int(game.get("port", 0)) == 24691 and int(game.get("max", 0)) == 12:
				found = true
		if not _check(found, "custom host appears in the shared server list with the correct game port"):
			return
	await get_tree().create_timer(3.0).timeout
	Net.leave(false)
	print("CUSTOM_PROBE PASS ", role)
	get_tree().quit()
