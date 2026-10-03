extends Node
## Screenshots of the real game at given spots (HUD hidden), two frames per spot with the hero nudged a few
## centimetres between them, so surfaces that fight for the same depth (they flicker in play) show as a difference.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_spots.tscn -- --class=knight --slot=97 \
##       --map=agdao --spots="0,13.6,-40;30,13.6,-40" --out=<dir> [--tag=after]
## Prints, per spot, the share of pixels that changed strongly between the two frames.

var args := {}
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(30)
	p = Game.player as Player
	Game.god_mode = true
	var map_id := StringName(args.get("map", "agdao"))
	if Game.current_map_id != map_id:
		Game.travel(map_id, &"start")
		await _wait(5)
		for i in 1500:
			await get_tree().process_frame
			if not Game.travelling and Game.current_map_id == map_id:
				break
		await _wait(40)
	var out := String(args.get("out", "user://spots"))
	DirAccess.make_dir_recursive_absolute(out)
	var tag := String(args.get("tag", "shot"))
	var i := 0
	for spec in String(args.get("spots", "0,0,0")).split(";", false):
		var v := spec.split(",")
		var at := Vector3(float(v[0]), float(v[1]), float(v[2]))
		for k in 40:
			await _wait(15)
			if CutscenePlayer.is_playing():
				CutscenePlayer.active.skip_all()
			elif k > 8:
				break
		for e in get_tree().get_nodes_in_group(&"enemy"):
			(e as Node).queue_free()
		p.teleport_to(at + Vector3.UP * 0.2)
		await _wait(60)
		Game.ui_root.visible = false
		await _wait(3)
		await RenderingServer.frame_post_draw
		var a := get_viewport().get_texture().get_image()
		p.global_position += Vector3(0.03, 0, 0.02)
		await _wait(3)
		await RenderingServer.frame_post_draw
		var b := get_viewport().get_texture().get_image()
		Game.ui_root.visible = true
		a.save_png(out.path_join("%s_%02d.png" % [tag, i]))
		print("SPOT %d %s changed=%.3f%%" % [i, spec, _changed(a, b) * 100.0])
		if args.has("diff"):
			_mask(a, b).save_png(out.path_join("%s_%02d_diff.png" % [tag, i]))
		i += 1
	get_tree().quit()

## Share of pixels whose brightness jumps by more than a third between the two frames (sampled every 2nd pixel).
func _changed(a: Image, b: Image) -> float:
	var n := 0
	var hit := 0
	for y in range(0, a.get_height(), 2):
		for x in range(0, a.get_width(), 2):
			n += 1
			if absf(a.get_pixel(x, y).get_luminance() - b.get_pixel(x, y).get_luminance()) > 0.33:
				hit += 1
	return float(hit) / maxf(1.0, n)

## The frame with every strongly changed pixel painted red (where the flicker is).
func _mask(a: Image, b: Image) -> Image:
	var m := a.duplicate() as Image
	m.adjust_bcs(0.6, 1.0, 0.3)
	for y in a.get_height():
		for x in a.get_width():
			if absf(a.get_pixel(x, y).get_luminance() - b.get_pixel(x, y).get_luminance()) > 0.33:
				m.set_pixel(x, y, Color(1, 0, 0))
	return m

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
