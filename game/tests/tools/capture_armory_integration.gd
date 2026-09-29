extends Node
## Real boot/gameplay and 60-second rendered observation. Uses hidden save slot 96.
var out := "res://../work/lemondev/tempo-armory/evidence/integration"
var frames_ms: Array[float] = []
var checks := 0
var failures: Array[String] = []

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()

func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _shot(label: String) -> void:
	for i in 12:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))

func _run() -> void:
	out = ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(out)
	get_window().size = Vector2i(1920, 1080)
	get_window().content_scale_size = Vector2i(1920, 1080)
	var main := load("res://src/main.gd").new() as Node
	main.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(main)
	for i in 3000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	_check(Game.in_session, "cold boot enters a game")
	print("INTEGRATION boot")
	if not Game.in_session:
		get_tree().quit(1)
		return
	Game.god_mode = true
	var h := Game.hero
	var player := Game.player as Player
	h.set_tier(DataGuilds.MAX_RANK)
	for attr in BH.ATTRIBUTES:
		h.progress.allocated[attr] = 100
	h.progress.points_changed.emit()
	var ids := [&"ashwood_crossbow", &"artisan_clockwork_cam_bow", &"artisan_serpent_kris_dagger", &"artisan_harbor_basket_sword", &"artisan_gothic_window_axe"]
	for id in ids:
		var item := DB.make_item(id, BH.Rarity.COMMON, 60, 73)
		h.inventory.add(item)
		_check(h.equip_from_inventory(item, &"main_weapon") == "", "equip " + String(id))
		player.ensure_stats()
		await _shot(String(id) + "-gameplay")
		_check(player.visual != null, "character visual ready")
	var set_data := preload("res://src/data/data_boss_sets.gd")
	for slot in set_data.slots_for_set(&"truth_of_raikuru"):
		var piece := DB.make_item(set_data.piece_id(&"truth_of_raikuru", slot), BH.Rarity.MASTER, 60, 188)
		h.inventory.add(piece)
		_check(h.equip_from_inventory(piece, slot) == "", "wear Raikuru " + String(slot))
	player.ensure_stats()
	_check(h.equipment.set_counts().get(&"truth_of_raikuru", 0) == 12, "complete set counted")
	_check(player.stats.has_flag(&"crit_lightning"), "complete set bonus active")
	await _shot("truth-of-raikuru-gameplay")
	var shield := DB.make_item(&"warden_kite_shield", BH.Rarity.COMMON, 1, 74)
	_check(shield != null and h.equipment.check(shield, &"sub_weapon", 60, h.progress.base_attributes()) != "", "crossbow prevents shield")
	var tempo_win := Game.ui_root.window(&"tempos") as TempoWindow
	if h.tempos.is_empty():
		var tempo := TempoRules.legend_data(&"kavira")
		tempo.uid = 909
		h.tempos.append(tempo)
	for t in h.tempos:
		t.fallen = true
	tempo_win.open()
	await _shot("tempo-over-game")
	_check(get_viewport().get_visible_rect().encloses(tempo_win._frame.get_global_rect()), "Tempo fits over live game")
	tempo_win.close_window()
	await get_tree().create_timer(0.3).timeout
	for cycle in 3:
		print("INTEGRATION pause cycle ", cycle)
		get_tree().paused = true
		var before := player._time
		for frame in 4:
			await get_tree().process_frame
		_check(player._time == before, "pause freezes gameplay")
		get_tree().paused = false
		for frame in 4:
			await get_tree().physics_frame
		_check(player._time > before, "resume restarts gameplay")
	# Warm shaders and animation before timing. Sample actual rendered frame intervals.
	print("INTEGRATION warmup")
	for i in 240:
		await get_tree().process_frame
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	print("INTEGRATION timed observation")
	var start := Time.get_ticks_usec()
	var previous := start
	var next_attack := start
	var attacks := 0
	while Time.get_ticks_usec() - start < 60000000:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		frames_ms.append((now - previous) / 1000.0)
		previous = now
		if now >= next_attack and player.action == null:
			player._start_light()
			attacks += 1
			next_attack = now + 1000000
	frames_ms.sort()
	_check(attacks >= 10, "repeated crossbow firing runs")
	_check(player.stats.loadout.main_type.id == &"crossbow" and not player.stats.loadout.has_shield, "legal crossbow loadout after observation")
	var over_budget := frames_ms.filter(func(ms): return ms > 16.67).size()
	var report := {"engine": Engine.get_version_info().string, "gpu": RenderingServer.get_video_adapter_name(),
		"renderer": RenderingServer.get_current_rendering_method(), "resolution": [1920,1080], "map": String(Game.current_map_id),
		"duration_seconds": (Time.get_ticks_usec() - start) / 1000000.0, "frames": frames_ms.size(), "attacks": attacks,
		"p95_ms": frames_ms[int(frames_ms.size()*0.95)], "p99_ms": frames_ms[int(frames_ms.size()*0.99)],
		"max_ms": frames_ms.back(), "frames_over_16_67ms": over_budget,
		"checks": checks, "failures": failures, "performance_gate": "PASS" if frames_ms[int(frames_ms.size()*0.95)] <= 16.67 else "UNVERIFIED_TARGET_NOT_MET"}
	FileAccess.open(out.path_join("report.json"), FileAccess.WRITE).store_string(JSON.stringify(report, "  "))
	FileAccess.open(out.path_join("frame-intervals-ms.json"), FileAccess.WRITE).store_string(JSON.stringify(frames_ms))
	print("ARMORY_INTEGRATION ", JSON.stringify(report))
	get_tree().quit(0 if failures.is_empty() else 1)
