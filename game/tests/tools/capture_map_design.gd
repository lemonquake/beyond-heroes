extends Node
## Map-design pass (2026-10-03) evidence: the real game (HUD, NPCs, lights) walked to fixed viewpoints, one shot with the
## HUD and one clean world view each. The same views run on the frozen baseline copy and on the candidate, so before and
## after match: same camera (the gameplay camera follows the hero), same time, same quality, same window.
##   godot --path game res://tests/tools/capture_map_design.tscn -- --class=knight --slot=96 --set=towns --tag=after \
##       --lite=0 --w=1600 --h=900 --out=<dir>
## --set: towns | zarael | interiors | story | dungeons | all.  --lite: 0 High (desktop preset), 1 Low (efficiency preset).
## Nothing is saved: hidden slot 96, settings changed in memory only.

const SETS := {
	"towns": [
		["sanctuary", "mal_01_gate", Vector3(0, 0, 33.0)], ["sanctuary", "mal_02_plaza", Vector3(0, 0, 11.0)],
		["sanctuary", "mal_03_market", Vector3(14.0, 0, 24.0)], ["sanctuary", "mal_04_terrace", Vector3(0, 2.0, -22.0)],
		["sanctuary", "mal_05_tavern_yard", Vector3(-22.0, 0, 8.0)], ["sanctuary", "mal_06_hald_garden", Vector3(-15.0, 0, 30.0)],
		["westreach", "wr_01_fields", Vector3(32.0, 0, 98.0)], ["westreach", "wr_02_mill", Vector3(0.0, 0, -12.0)],
		["westreach", "wr_03_cove", Vector3(-176.0, 0, 99.0)],
		["olivar", "ol_01_plaza", Vector3(0, 0, 10.0)], ["olivar", "ol_02_docks", Vector3(0.0, 0, -37.0)],
		["olivar", "ol_03_apothecary", Vector3(-22.0, 0, -6.0)],
		["wyman_outpost", "wy_01_bonfire", Vector3(-4.0, 0, 5.0)], ["wyman_outpost", "wy_02_jetty", Vector3(30.0, 0, 26.0)],
		["wyman_outpost", "wy_03_forge", Vector3(12.0, 0, 15.0)],
		["ruined_forest", "rf_01_arrival", Vector3(-56.0, 0, 12.0)], ["ruined_forest", "rf_02_village", Vector3(-30.0, 0, 8.0)],
		["ruined_forest", "rf_03_camp", Vector3(18.0, 0, -6.0)],
		["weeping_causeway", "wc_01_causeway", Vector3(-40.0, 0, 0)], ["sundered_reach", "sr_01_arrival", Vector3(0, 0, 20.0)],
	],
	"zarael": [
		["agdao", "ag_01_pier", Vector3(-20.0, 1.6, 46.0)], ["agdao", "ag_02_harbour", Vector3(-40.0, 1.6, 42.0)],
		["agdao", "ag_03_market", Vector3(0, 5.6, 25.0)], ["agdao", "ag_04_middle", Vector3(-22.0, 9.6, -2.0)],
		["agdao", "ag_05_upper", Vector3(40.0, 13.6, -24.0)], ["agdao", "ag_06_crown", Vector3(0, 17.6, -46.0)],
		["agdao", "ag_07_gate", Vector3(70.0, 13.6, -26.0)],
		["zr_coilwood", "zc_01_shrine", Vector3(-100.0, 0, 14.0)], ["zr_coilwood", "zc_02_aqueduct", Vector3(-84.0, 0, 12.0)],
		["zr_barrens", "zb_01_camp", Vector3(-40.0, 0, 40.0)], ["zr_barrens", "zb_02_colossus", Vector3(40.0, 0, -26.0)],
		["bridge_of_death", "bd_01_south", Vector3(0, 0, 120.0)], ["zr_citadel", "hc_01_siege", Vector3(0, 0, 66.0)],
		["zr_citadel", "hc_02_avenue", Vector3(0, 0, 40.0)],
	],
	"interiors": [
		["int_tavern", "in_tavern_door", Vector3(2.0, 0, 4.4)], ["int_tavern", "in_tavern_room", Vector3(1.0, 0, 0.5)],
		["int_guildhouse", "in_guild_door", Vector3(0, 0, 6.2)], ["int_guildhouse", "in_guild_hall", Vector3(4.0, 0, 0.5)],
		["int_swordfin", "in_swordfin", Vector3(-1.0, 0, 2.5)], ["int_lantern", "in_lantern", Vector3(-1.0, 0, 2.0)],
		["int_netmender", "in_netmender", Vector3(1.0, 0, 2.2)], ["int_cartographer", "in_cartographer", Vector3(-1.0, 0, 2.0)],
		["int_widow", "in_widow", Vector3(1.0, 0, 2.2)], ["int_keeper", "in_keeper", Vector3(-1.0, 0, 2.0)],
		["int_refugee", "in_refugee", Vector3(0.5, 0, 2.2)],
	],
	"story": [
		["catacombs", "st_cat_guard", Vector3(0, 0, 3.0)], ["catacombs", "st_cat_cistern", Vector3(24.0, 0, -6.0)],
		["catacombs", "st_cat_west", Vector3(-26.0, 0, -12.0)], ["catacombs", "st_cat_ritual", Vector3(0, 0, -32.0)],
		["forgotten_temple", "st_tmp_nave", Vector3(0, 0, -6.0)], ["forgotten_temple", "st_tmp_library", Vector3(14.0, 0, -12.0)],
		["forgotten_temple", "st_tmp_sanctum", Vector3(0, 2.0, -28.0)], ["boss_arena", "st_throne_arrival", Vector3(0, 0, 31.0)],
	],
	# dungeon views use the floor's own spawns (arrival, then its way on)
	"dungeons": [
		["dg_deeps_2", "dg_deeps_2"], ["dg_warren_2", "dg_warren_2"], ["dg_ember_3", "dg_ember_3"], ["dg_barrow_2", "dg_barrow_2"],
		["dg_orrery_2", "dg_orrery_2"], ["dg_jade_sepulchre_3", "dg_jade_3"], ["dg_obsidian_engine_3", "dg_obsidian_3"],
		["dg_veinworks_7", "dg_vein_7"], ["dg_ossuary_2", "dg_ossuary_2"], ["dg_reliquary_3", "dg_reliquary_3"],
		["dg_cellars_1", "dg_cellars_1"], ["dg_burrows_2", "dg_burrows_2"], ["dg_warcamp_1", "dg_warcamp_1"],
		["dg_hive_2", "dg_hive_2"], ["dg_sump_2", "dg_sump_2"], ["dg_briar_2", "dg_briar_2"], ["dg_dunemourn_2", "dg_dunemourn_2"],
		["dg_thunderwell_2", "dg_thunderwell_2"], ["dg_undercroft_2", "dg_undercroft_2"], ["dg_geode_2", "dg_geode_2"],
		["dg_vault_2", "dg_vault_2"], ["dg_wyrmcoil_3", "dg_wyrmcoil_3"], ["dg_maw_3", "dg_maw_3"], ["dg_prismheart_5", "dg_prismheart_5"],
		["dg_underworld_6", "dg_underworld_6"], ["dg_aetherreach_7", "dg_aetherreach_7"], ["dg_eclipse_7", "dg_eclipse_7"],
		["dg_solarium_8", "dg_solarium_8"],
	],
}

var args := {}
var out := ""
var main: Node
var notes := {"shots": []}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/map-design-20261003/captures")))
	DirAccess.make_dir_recursive_absolute(out)
	Game.save_slot = 96
	Settings.resolution = 0
	Settings.window_mode = 0
	if args.get("lite", "0") == "1":
		Settings._efficiency_preset()
	else:
		Settings._desktop_preset()
	main = load("res://src/main.tscn").instantiate()
	add_child(main)
	_run.call_deferred()

func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds, true).timeout

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	notes.shots.append(label)
	print("SHOT ", label)

func _ground(p: Node3D, at: Vector3) -> Vector3:
	var q := PhysicsRayQueryParameters3D.create(Vector3(at.x, at.y + 6.0, at.z), Vector3(at.x, at.y - 30.0, at.z), BH.LAYER_WORLD | BH.LAYER_GROUND)
	var hit := p.get_world_3d().direct_space_state.intersect_ray(q)
	return (hit.position as Vector3) + Vector3(0, 0.1, 0) if not hit.is_empty() else at

func _run() -> void:
	await _wait(2.0)
	for i in 300:
		if Game.in_session and Game.player is Player and (Game.player as Player).hero:
			break
		await _wait(0.1)
	get_window().size = Vector2i(int(args.get("w", "1600")), int(args.get("h", "900")))
	Game.god_mode = true
	await _wait(1.0)
	notes["engine"] = Engine.get_version_info().string
	notes["renderer"] = RenderingServer.get_current_rendering_method()
	notes["adapter"] = RenderingServer.get_video_adapter_name()
	notes["lite"] = Settings.lite
	notes["window"] = [get_window().size.x, get_window().size.y]
	var tag := String(args.get("tag", "after"))
	var q := "low" if Settings.lite else "high"
	var which := String(args.get("set", "towns"))
	var sets: Array = SETS.keys() if which == "all" else which.split(",")
	for s in sets:
		for v in SETS[s]:
			await _view(v, s == "dungeons", "%s_%s" % [tag, q])
	var f := FileAccess.open(out.path_join("notes_%s_%s_%s.json" % [which, tag, q]), FileAccess.WRITE)
	f.store_string(JSON.stringify(notes, "  "))
	f.close()
	get_tree().quit()

func _view(v: Array, dungeon: bool, suffix: String) -> void:
	var p := Game.player as Player
	var mid := StringName(v[0])
	if Game.current_map_id != mid:
		Game.load_map(mid, &"start")
		await _wait(2.0)
	for k in 20:
		if not CutscenePlayer.is_playing():
			break
		CutscenePlayer.active.skip_all()
		await _wait(0.5)
	for e in get_tree().get_nodes_in_group(&"enemy"):
		(e as Node).queue_free()          # the dressing, not the fight: enemies would block the views
	var spots: Array = []
	if dungeon:
		for sp in [&"arrival", &"descent", &"exit"]:
			if Game.current_map.spawns.has(sp):
				spots.append([String(sp), (Game.current_map.spawns[sp] as Node3D).global_position])
	else:
		spots.append(["", v[2]])
	for s in spots:
		p.global_position = _ground(p, s[1])
		p.velocity = Vector3.ZERO
		await _wait(1.6)
		var label := String(v[1]) + ("_" + String(s[0]) if s[0] != "" else "")
		Game.ui_root.visible = true
		await _shot("%s__%s_hud" % [label, suffix])
		Game.ui_root.visible = false
		await _wait(0.2)
		await _shot("%s__%s_clean" % [label, suffix])
		Game.ui_root.visible = true
