extends Node
## bh-021 evidence: boot the real game (hidden save slot), play a story cutscene, and screenshot every scene at a few
## points of its timeline (real renderer, real UI).
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh021_cutscene.tscn -- --class=knight --slot=97
##         --map=olivar --cs=the_three [--at=0.3,0.75] [--flags=mq_shard_taken] [--out=<dir>] [--skip=2]
## --skip=N presses Skip scene N times at random points (checks the skip path), --only=3,4 shoots only those scenes.

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var cs_id := StringName(args.get("cs", "the_three"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-021/evidence/cutscenes/" + String(cs_id))))
	DirAccess.make_dir_recursive_absolute(out)
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(40)
	for f in String(args.get("flags", "")).split(",", false):
		Game.hero.world_flags[StringName(f)] = true
	if args.has("pos"):
		var p := String(args.pos).split(",")
		(Game.player as Player).teleport_to(Game.current_map.to_global(Vector3(float(p[0]), 0.3, float(p[1]))))
		await _wait(30)
	var fracs: Array = []
	for f in String(args.get("at", "0.3,0.75")).split(","):
		fracs.append(float(f))
	var only: Array = []
	for f in String(args.get("only", "")).split(",", false):
		only.append(int(f))
	var c := DataCutscenes.make(cs_id)
	if args.has("anchor"):
		var p := String(args.anchor).split(",")
		c.set_meta(&"at", Game.current_map.global_transform * Transform3D(Basis(Vector3.UP, deg_to_rad(float(p[2]))), Vector3(float(p[0]), 0, float(p[1]))))
	var t0 := Time.get_ticks_msec()
	var cp := CutscenePlayer.play_cutscene(c)
	var shot_done := {}
	var skips := int(args.get("skip", "0"))
	var state := {"done": false}
	cp.finished.connect(func(_id) -> void: state.done = true)
	if args.has("start"):
		cp.jump_to(int(args.start) - 1)
	while not state.done and Time.get_ticks_msec() - t0 < 400000:
		await get_tree().process_frame
		if not is_instance_valid(cp) or cp.index < 0 or cp.index >= cp.scenes.size():
			continue
		var idx := cp.index
		var u := cp.t / maxf(cp.length, 0.01)
		for k in fracs.size():
			var key := "%d_%d" % [idx, k]
			if shot_done.has(key) or u < float(fracs[k]):
				continue
			shot_done[key] = true
			if only.is_empty() or only.has(idx + 1):
				await RenderingServer.frame_post_draw
				var name := "%02d_%s_%d" % [idx + 1, String(cp.scenes[idx].name).to_lower().replace(" ", "_").replace("'", ""), int(float(fracs[k]) * 100)]
				get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
				print("BH021 CS SHOT ", name)
		if skips > 0 and u > 0.5 and idx % 3 == 1:
			skips -= 1
			print("BH021 CS SKIP scene ", idx + 1)
			cp.skip_scene()
	print("BH021 CS DONE %s in %.1f s, flags: %s" % [cs_id, (Time.get_ticks_msec() - t0) / 1000.0, Game.hero.world_flags.keys()])
	await _wait(30)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("zz_after.png"))
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
