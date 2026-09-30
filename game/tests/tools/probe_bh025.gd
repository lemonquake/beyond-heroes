extends Node
## bh-025 probe: the music director in the live game. Boots a hero on a scratch slot and walks the layers:
## town -> the road -> a fight -> calm again -> Paul David -> a dungeon; prints what plays and saves screenshots.
##   godot --path game res://tests/tools/probe_bh025.tscn -- --class=knight --map=sanctuary --slot=97

var out := "res://../work/lemondev/bh-025/evidence"
var fails := 0

func _ready() -> void:
	_run.call_deferred()

func _frames(count: int) -> void:
	for i in count:
		await get_tree().process_frame

func _wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout

func _shot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))

func _check(what: String, want: StringName) -> void:
	var p: AudioStreamPlayer = Music._players.get(Music.current())
	var good := Music.current() == want and p != null and p.playing
	if not good:
		fails += 1
	print("%s  %-34s playing %-20s at %5.1f s, %5.1f dB (music bus %.0f %%)" % ["ok  " if good else "FAIL", what, Music.current(),
		p.get_playback_position() if p else -1.0, p.volume_db if p else -99.0, Settings.music_volume * 100.0])

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var main := load("res://src/main.gd").new() as Node
	add_child(main)
	for i in 2000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	Game.god_mode = true
	await _wait(3.0)
	_check("Malasugue Town", &"main_theme")

	await Game.travel(&"westreach", &"start")
	await _wait(3.0)
	_check("Westreach, nobody near", &"main_theme")
	var road_pos: float = Music._players[&"main_theme"].get_playback_position()
	var foe: Enemy = null
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.alive and not e.is_boss and (foe == null
				or e.global_position.distance_to(Game.player.global_position) < foe.global_position.distance_to(Game.player.global_position)):
			foe = e
	Game.player.teleport_to(foe.global_position + Vector3(2.5, 0.2, 0))
	await _wait(3.5)
	_check("a fight on the road", &"battle_theme")
	await _shot("westreach_fight")
	Settings.combat_music = false
	await _wait(2.5)
	_check("the same fight, Battle Music off", &"main_theme")
	Settings.combat_music = true
	await _wait(2.0)
	_check("Battle Music on again", &"battle_theme")
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.alive and e.brain.is_engaged():
			e.die(Game.player)
	await _wait(Music.CALM_HOLD + 5.0)
	_check("the fight is over", &"main_theme")
	var back: float = Music._players[&"main_theme"].get_playback_position()
	print("     the road's music carried on: left at %.1f s, now at %.1f s" % [road_pos, back])
	if back < road_pos:
		fails += 1

	await Game.travel(&"olivar", &"start")
	await _wait(2.0)
	_check("Olivar", &"main_theme")
	var paul: Npc = null
	for n in get_tree().get_nodes_in_group(&"npc"):
		if n.def.id == &"paul_david":
			paul = n
	Game.player.teleport_to(paul.global_position + Vector3(0, 0.2, 2.5))
	await _frames(30)
	Game.ui_root.dialogue.start(paul, "hub_before")
	await _wait(2.5)
	_check("Paul David, small talk", &"main_theme")
	Game.ui_root.dialogue.session._enter("roydo")
	await _wait(3.0)
	_check("Paul David speaks of Roydo", &"aljay_theme")
	await _shot("paul_david_aljay_theme")
	Game.ui_root.dialogue.close()
	await _wait(0.5)
	CutscenePlayer.play(&"the_three", func() -> void: pass)
	await _wait(4.0)
	_check("the tale of the three (cutscene)", &"aljay_theme")
	while CutscenePlayer.is_playing():          # this one is skipped scene by scene, never as a whole
		CutscenePlayer.active.skip_scene()
		await _wait(0.6)
	await _wait(4.0)
	_check("after the tale", &"main_theme")

	var ember := &""
	var defs := DataDungeons.defs()
	for id in defs:
		if defs[id].get("theme", &"") == &"ember":
			ember = id
	await Game.travel(DataDungeons.map_id(ember, 1), &"arrival")
	await _wait(3.0)
	_check("the ember dungeon", &"fire_dungeon_theme")
	await _shot("ember_dungeon")

	Game.ui_root.open(&"settings")
	await _frames(10)
	for w in Game.ui_root.find_children("*", "SettingsWindow", true, false):
		w._tabs.current_tab = 1
	await _frames(20)
	await _shot("settings_audio")
	print("PROBE %s (%d failed)" % ["PASSED" if fails == 0 else "FAILED", fails])
	get_tree().quit(1 if fails else 0)
