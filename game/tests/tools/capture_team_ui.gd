extends Node

func _ready() -> void:
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func _run() -> void:
	for i in 600:
		if Game.in_session and not Game.travelling:
			break
		await get_tree().create_timer(0.1).timeout
	await get_tree().create_timer(3.0).timeout
	Game.god_mode = true
	Net.host_game(24686)
	Net.set_process(false)
	Net.peers[20] = {"name": "Scout with a long name", "cls": "ranger", "level": 24, "map": "westreach", "device": "Mobile"}
	Net.peers[30] = {"name": "Mage", "cls": "mage", "level": 21, "map": "ruined_forest", "device": "PC"}
	Net.peers[40] = {"name": "Shadowblade", "cls": "shadowblade", "level": 22, "map": "sanctuary", "device": "PC"}
	Game.ui_root.open(&"multiplayer")
	await get_tree().create_timer(1.0).timeout
	await RenderingServer.frame_post_draw
	var suffix := "touch" if Settings.touch_mode else "desktop"
	get_viewport().get_texture().get_image().save_png("res://../output/team-ui-%s.png" % suffix)
	print("TEAM_UI %s captured" % suffix)
	Net.peers = {1: Net._profile()}
	Net.leave(false)
	get_tree().quit()
