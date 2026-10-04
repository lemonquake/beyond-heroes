extends Node
## Class Transcendence armours in the real game: for each identity of one family, the hero takes that class (path set in
## place, then the Grand Master's refresh) and wears its class armour with plain matching legs, boots and gloves; one
## shot from the front and one from behind, close up, HUD hidden.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_transcend_armor.tscn -- --class=knight --level=130
##       --slot=95 --out=<dir>

const OUTFIT := {
	&"knight": [&"iron_cuisses", &"iron_sabaton", &"iron_gauntlet"],
	&"ranger": [&"hide_leggings", &"soft_boot", &"runed_glove"],
	&"mage": [&"linen_trousers", &"soft_boot", &"silk_glove"],
	&"shadowblade": [&"cutpurse_trousers", &"soft_boot", &"runed_glove"],
}

var out := ""
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	if out == "":
		out = ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence/armor")
	DirAccess.make_dir_recursive_absolute(out)
	Settings.first_person = false
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 2000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	p.set_first_person(false)
	Game.god_mode = true
	for t in TempoParty.actors(get_tree()):
		t.visible = false
	var fam := p.hero.cls.id
	var first: StringName = DataTranscendence.children_of(fam)[0]
	var paths: Array = [[first]]
	for m in DataTranscendence.children_of(first):
		paths.append([first, m])
	var eq := p.hero.equipment
	eq.slots[&"helm"] = null
	for id in OUTFIT[fam]:
		var it := DB.make_item(id, BH.Rarity.ELITE, 120, 11)
		var slot := eq.auto_slot(it)
		eq.slots[slot] = it
		if slot == &"gloves_1" or slot == &"boots_1":
			eq.slots[StringName(String(slot).replace("_1", "_2"))] = DB.make_item(id, BH.Rarity.ELITE, 120, 12)
	p.camera._dist_target = 4.2
	Game.ui_root.visible = false
	for path in paths:
		var id: StringName = path.back()
		p.hero.transcendence_path.assign(path)
		p.refresh_class_look()
		var armor_id: StringName = (DataTranscendence.info(id).gear as Array).filter(func(g): return DB.item_base(g).category == &"armor")[0]
		eq.slots[&"armor"] = DB.make_item(armor_id, BH.Rarity.ELITE, 125, 13)
		p.refresh_equipment_visuals()
		p.mark_stats_dirty()
		await _wait(20)
		p.face_toward(p.camera.global_position)
		await _wait(30)
		await _shot("%s_%s_front" % [String(fam), String(id)])
		p.face_toward(p.global_position * 2.0 - p.camera.global_position)
		await _wait(30)
		await _shot("%s_%s_back" % [String(fam), String(id)])
	get_tree().quit()

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("SHOT ", label)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
