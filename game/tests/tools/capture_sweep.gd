extends Node
## bh-038: walks a grid over a whole map in the real game and photographs every walkable spot twice (the hero nudged a
## few centimetres between frames), like capture_spots but finding the ground itself. Per spot it prints
##   SPOT <i> x,y,z changed=<% of pixels that flicker> black=<% of near-black pixels below the horizon>
## and keeps the frames of spots over the thresholds (with --diff, a red mask of the flicker too).
##   godot --path game --resolution 1280x720 res://tests/tools/capture_sweep.tscn -- --class=knight --slot=97 \
##       --map=zr_barrens --rect="-140,-120,140,90" --step=20 --out=<dir> [--tag=before] [--all] [--diff]
## --spots="x,z;x,z" replaces the grid. A spot with no ground under it (sea, gorge) is skipped.

var args := {}
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
		elif a.begins_with("--"):
			args[a.substr(2)] = "1"
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
	for k in 40:
		await _wait(15)
		if CutscenePlayer.is_playing():
			CutscenePlayer.active.skip_all()
		elif k > 8:
			break
	var out := String(args.get("out", "user://sweep"))
	DirAccess.make_dir_recursive_absolute(out)
	var tag := String(args.get("tag", "shot"))
	var flicker_min := float(args.get("flicker", "0.4"))
	var black_min := float(args.get("black", "1.5"))
	var spots: Array[Vector2] = []
	if args.has("spots"):
		for spec in String(args.spots).split(";", false):
			var v := spec.split(",")
			spots.append(Vector2(float(v[0]), float(v[1])))
	else:
		var r := String(args.get("rect", "-100,-100,100,100")).split(",")
		var step := float(args.get("step", "20"))
		var z := float(r[1])
		while z <= float(r[3]) + 0.01:
			var x := float(r[0])
			while x <= float(r[2]) + 0.01:
				spots.append(Vector2(x, z))
				x += step
			z += step
	var i := 0
	var worst := []
	for s in spots:
		var g := _ground(s)
		if is_nan(g):
			continue
		for e in get_tree().get_nodes_in_group(&"enemy"):
			(e as Node).queue_free()
		var at := Game.current_map.to_global(Vector3(s.x, g, s.y))
		p.teleport_to(at + Vector3.UP * 0.2)
		await _wait(40)
		if CutscenePlayer.is_playing():
			CutscenePlayer.active.skip_all()
			await _wait(20)
		Game.ui_root.visible = false
		await _wait(3)
		await RenderingServer.frame_post_draw
		var a := get_viewport().get_texture().get_image()
		p.global_position += Vector3(0.03, 0, 0.02)
		await _wait(3)
		await RenderingServer.frame_post_draw
		var b := get_viewport().get_texture().get_image()
		Game.ui_root.visible = true
		var ch := _changed(a, b) * 100.0
		var bl := _black(a) * 100.0
		var name := "%s_%03d" % [tag, i]
		print("SPOT %d %.0f,%.1f,%.0f changed=%.3f%% black=%.2f%%" % [i, s.x, g, s.y, ch, bl])
		if args.has("all") or ch >= flicker_min or bl >= black_min:
			a.save_png(out.path_join(name + ".png"))
			if args.has("diff") and ch >= flicker_min:
				_mask(a, b).save_png(out.path_join(name + "_diff.png"))
		worst.append([ch, bl, i, s])
		i += 1
	print("SWEEP %s spots=%d" % [map_id, i])
	get_tree().quit()

## Height of the walkable surface at map-local (x, z), or NAN when nothing solid is under it.
func _ground(s: Vector2) -> float:
	var map := Game.current_map
	var space := map.get_world_3d().direct_space_state
	var from := map.to_global(Vector3(s.x, 120.0, s.y))
	var q := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 260.0, BH.LAYER_GROUND | BH.LAYER_WORLD)
	var hit := space.intersect_ray(q)
	if hit.is_empty():
		return NAN
	return hit.position.y - map.global_position.y

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

## Share of near-black pixels in the lower two thirds of the frame (ground and props; the sky is above).
func _black(a: Image) -> float:
	var n := 0
	var hit := 0
	for y in range(a.get_height() / 3, a.get_height(), 3):
		for x in range(0, a.get_width(), 3):
			n += 1
			var c := a.get_pixel(x, y)
			if maxf(c.r, maxf(c.g, c.b)) < 0.035:
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
