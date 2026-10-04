extends Node
## bh-038: the crystal spirits (GemSpirits) in the real game. Equips the hero's main weapon with sets of crystals and
## photographs the weapon close up (a capture camera beside the hero) and from the normal game camera.
##   godot --path game --resolution 1280x720 res://tests/tools/capture_gems.tscn -- --class=knight --slot=96 \
##       --out=<dir> [--map=agdao] [--weapon=runed_sword] [--sets="ember_orbital,nova_orbital,sora_orbital;..."]

const SETS := "ember_orbital,nova_orbital,sora_orbital;aqua_orbital,thundra_orbital,vipera_orbital;bloodrift_orbital,essencerift_orbital,aetherift_orbital;luna_orbital,sol_orbital,airah_orbital;ember_fragment,aqua_shard,nova_crystalline,thundra_orbital,vipera_orbital,bloodrift_shard,luna_crystalline,sol_orbital"

var args := {}

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
	var out := String(args.get("out", "user://gems"))
	DirAccess.make_dir_recursive_absolute(out)
	var p := Game.player as Player
	var cam := Camera3D.new()
	cam.fov = 40.0
	get_tree().root.add_child(cam)
	var i := 0
	for spec in String(args.get("sets", SETS)).split(";", false):
		for e in get_tree().get_nodes_in_group(&"enemy"):
			(e as Node).queue_free()
		var gems := spec.split(",", false)
		var it := DB.make_item(StringName(args.get("weapon", "runed_sword")), BH.Rarity.AETHER if gems.size() > 3 else BH.Rarity.LEGENDARY, 60, 11)
		it.sockets = gems.size()
		it.gems = []
		for g in gems:
			it.gems.append(g)
		p.hero.equipment.slots[&"main_weapon"] = it
		p.refresh_equipment_visuals()
		await _wait(30)
		var spirits := p.visual.find_children("GemSpirits", "Node3D", true, false)
		print("SET %d %s spirits=%s families=%s" % [i, spec, spirits.size(), (spirits[0] as GemSpirits).families() if spirits.size() > 0 else []])
		# close up: from the hero's front-right at weapon height, looking at the middle of the blade
		var w := p.visual.weapon_point(&"main", 0.55)
		var fwd := p.global_basis.z
		var right := p.global_basis.x
		cam.global_position = w + fwd * 1.5 + right * 0.6 + Vector3.UP * 0.35
		cam.look_at(w, Vector3.UP)
		cam.current = true
		Game.ui_root.visible = false
		for k in 2:
			await _wait(13)
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(out.path_join("gems_%02d_close_%d.png" % [i, k]))
		cam.current = false
		await _wait(5)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out.path_join("gems_%02d_game.png" % i))
		Game.ui_root.visible = true
		i += 1
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
