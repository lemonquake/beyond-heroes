extends Node
## Network payload sizes (bh-035): boots the real game on one map and measures what Net would put on the wire for this
## machine's allies and the map's monsters, without opening a connection. Also checks that the appearance signature
## Net uses to decide on a reliable re-send stays put while nothing is changed.
##   godot --headless --path game res://tests/tools/net_size_probe.tscn -- --class=knight --slot=97 --map=ruined_forest

var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 3000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	Game.god_mode = true
	for i in 60:
		await get_tree().process_frame
	var allies: Array = Net._local_allies()
	var sigs := {}
	var unstable := 0
	for f in 90:
		for pair in Net._local_allies():
			var a: Actor = pair[1]
			if a.visual == null:
				continue
			var sig := hash(str(a.visual.appearance)) ^ hash(String(a.visual._stance_idle))
			if sigs.has(pair[0]) and sigs[pair[0]] != sig:
				unstable += 1
			sigs[pair[0]] = sig
		await get_tree().process_frame
	var pack := []
	var app_bytes := 0
	for pair in allies:
		var a: Actor = pair[1]
		pack.append({"k": pair[0], "s": Net.actor_state(a), "n": a.display_name})
		if a.visual:
			app_bytes += var_to_bytes(a.visual.appearance).size()
	print("NETSIZE allies=%d ally_pack_bytes=%d appearance_bytes=%d appearance_sig_changes_over_90_frames=%d per_ally=%s" % [
		allies.size(), var_to_bytes([String(Game.current_map_id), pack]).size(), app_bytes, unstable, allies.map(func(p): return "%s:%d" % [p[0], var_to_bytes({"k": p[0], "s": Net.actor_state(p[1]), "n": p[1].display_name}).size()])])
	var states := []
	for e: Enemy in get_tree().get_nodes_in_group(&"enemy"):
		if not e.alive or e.net_replica:
			continue
		var v := e.visual
		states.append([1, e.global_position, e.rotation.y, e.velocity, e.hp, e.max_hp(), String(v.current_action() if v else &""),
			v.action_serial if v else 0, v.action_rate if v else 1.0, bool(v._action_loop) if v else false, e.brain.is_engaged(), e.shield_hp])
	var one := var_to_bytes(states.slice(0, 1)).size() if not states.is_empty() else 0
	var batch := var_to_bytes(["ruined_forest", 1, states.slice(0, 8)]).size() if not states.is_empty() else 0
	print("NETSIZE enemies=%d one_state_bytes=%d batch8_bytes=%d" % [states.size(), one, batch])
	get_tree().quit()
