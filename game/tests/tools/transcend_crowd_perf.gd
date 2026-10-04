extends Node
## Class Transcendence render cost: twelve other players' heroes (NetAvatars, the same path real remote heroes take)
## standing round the hero in Malasugue, dressed either in the twelve class armours (--variant=class) or in ordinary
## armour of the same kinds (--variant=plain: hauberk, robe, coat), the same legs, boots and gloves. After a warm-up the
## frame time, draw calls and primitives are sampled (vsync and the frame cap off); one JSON line is printed.
##   godot --path game --resolution 1280x720 res://tests/tools/transcend_crowd_perf.tscn -- --class=knight --level=130
##       --slot=95 --variant=class --profile=pc-low [--frames=300]

const CLASS_ARMOR := [&"tc_royal_guard_cuirass", &"tc_black_dominion_plate", &"tc_sanctified_plate", &"tc_trackers_leathers",
	&"tc_livingwood_leathers", &"tc_constellation_leathers", &"tc_arcanist_vestments", &"tc_archmage_robes", &"tc_riftwoven_robes",
	&"tc_nightstalker_leathers", &"tc_afterimage_mantle", &"tc_sanguine_leathers"]
const PLAIN_ARMOR := [&"warden_plate", &"warden_plate", &"warden_plate", &"traveler_coat", &"traveler_coat", &"traveler_coat",
	&"magister_robe", &"magister_robe", &"magister_robe", &"brigandine", &"brigandine", &"brigandine"]
const LEGS := [&"iron_cuisses", &"iron_cuisses", &"iron_cuisses", &"hide_leggings", &"hide_leggings", &"hide_leggings",
	&"linen_trousers", &"linen_trousers", &"linen_trousers", &"cutpurse_trousers", &"cutpurse_trousers", &"cutpurse_trousers"]

var variant := "class"
var frames := 300

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--variant="):
			variant = a.get_slice("=", 1)
		if a.begins_with("--frames="):
			frames = int(a.get_slice("=", 1))
		if a.begins_with("--profile="):
			match a.get_slice("=", 1):
				"pc-low":
					Settings._desktop_preset()
					Settings.shadows_quality = 0
					Settings.texture_quality = 0
					Settings.effects_quality = 0
					Settings.anti_aliasing = 0
				"mobile":
					Settings._efficiency_preset()
	Settings.first_person = false
	Settings.resolution = 0
	Settings.window_mode = 0
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 3000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	var p := Game.player as Player
	p.set_first_person(false)
	Game.god_mode = true
	Engine.max_fps = 0
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var armor: Array = CLASS_ARMOR if variant == "class" else PLAIN_ARMOR
	for i in 12:
		var av := NetAvatar.new().setup(900 + i, "p", {"name": "Hero %d" % (i + 1), "lvl": 130, "mhp": 1000.0, "hp": 1000.0})
		Game.current_map.add_child(av)
		var a := TAU * float(i) / 12.0
		av.global_position = p.global_position + Vector3(cos(a), 0, sin(a)) * 4.5
		var hands := &"iron_gauntlet" if i < 3 else (&"silk_glove" if i >= 6 and i < 9 else &"runed_glove")
		var feet := &"iron_sabaton" if i < 3 else &"soft_boot"
		av.set_appearance({"model": HeroLook.MODEL, "scale": 1.0, "tint": Color.WHITE, "pers": &"knight",
			"set_gear": {"armor": String(armor[i]), "leggings": String(LEGS[i]), "gloves_1": String(hands), "gloves_2": String(hands),
				"boots_1": String(feet), "boots_2": String(feet)}})
	await _wait(240)
	var samples: Array[float] = []
	var draws := 0.0
	var prims := 0.0
	var last := Time.get_ticks_usec()
	for i in frames:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		samples.append((now - last) / 1000.0)
		last = now
		draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		prims += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	samples.sort()
	var res := {"variant": variant, "renderer": RenderingServer.get_current_rendering_method(), "lite": Settings.lite,
		"window": [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y], "frames": frames,
		"median_ms": snappedf(samples[samples.size() / 2], 0.01), "p95_ms": snappedf(samples[int(samples.size() * 0.95)], 0.01),
		"draws": roundi(draws / frames), "prims": roundi(prims / frames), "gpu": RenderingServer.get_video_adapter_name()}
	print("CROWD ", JSON.stringify(res))
	get_tree().quit()

func _wait(n := 10) -> void:
	for i in n:
		await get_tree().process_frame
