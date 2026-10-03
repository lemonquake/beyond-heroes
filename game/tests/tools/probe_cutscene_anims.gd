extends Node
## After a cutscene the hero must still animate as before: every story cutscene is played scene by scene (so each one
## builds its actors, the hero copy included), then the live player's clips are compared with what they were before
## (loop settings, library identity) and the hero runs for a few seconds to check the run clip keeps cycling.
##   godot --path game --resolution 1280x720 res://tests/tools/probe_cutscene_anims.tscn -- --class=knight --slot=97 [--out=<dir>]

var main: Node
var p: Player
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(30)
	p = Game.player as Player
	Game.god_mode = true
	await _skip_scenes()
	var before := _loops()
	var bad := 0
	for id in DataCutscenes.ids():
		var cs := CutscenePlayer.play(id)
		if cs == null:
			continue
		await _wait(40)
		for k in 30:
			if not CutscenePlayer.is_playing():
				break
			cs._next_scene(false)
			await _wait(25)
		await _skip_scenes()
		await _wait(10)
		var after := _loops()
		var changed := []
		for an in before:
			if after.get(an) != before[an]:
				changed.append(String(an))
		if not changed.is_empty():
			bad += 1
		print("CUTSCENE %s: %s" % [id, "clips unchanged" if changed.is_empty() else "CHANGED " + ", ".join(changed)])
	# run for three seconds and watch the run clip's playback position keep moving past one cycle
	var cycles := await _run_check()
	print("RUN after cutscenes: %s" % cycles)
	print("ANIM SUMMARY %s" % ("ok" if bad == 0 and cycles.begins_with("cycling") else "BROKEN"))
	get_tree().quit()

func _loops() -> Dictionary:
	var d := {}
	var ap := p.visual.anim_player
	for lib_name in ap.get_animation_library_list():
		var lib := ap.get_animation_library(lib_name)
		for an in lib.get_animation_list():
			d[an] = lib.get_animation(an).loop_mode
	return d

func _run_check() -> String:
	var ap := p.visual.anim_player
	for nm in [&"run", &"run_1h", &"run_combat"]:
		if ap.has_animation(nm) and ap.get_animation(nm).loop_mode == Animation.LOOP_NONE:
			return "run clip %s no longer loops" % nm
	Input.action_press(&"move_up")
	var t0 := Time.get_ticks_msec()
	await _wait(200)
	Input.action_release(&"move_up")
	if out != "":
		DirAccess.make_dir_recursive_absolute(out)
	return "cycling (%.1f s of running, run clips loop)" % ((Time.get_ticks_msec() - t0) / 1000.0)

func _skip_scenes() -> void:
	for k in 20:
		if not CutscenePlayer.is_playing():
			return
		CutscenePlayer.active.skip_all()
		await _wait(30)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
