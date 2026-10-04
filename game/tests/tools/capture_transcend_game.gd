extends Node
## Class Transcendence evidence in the real game: Grand Master Edran Vale in the Guild House, the Class window at each
## stage (first advancement, master choice side by side, review, complete), the Skills and Talents pages (granted
## ranks, locked previews), an item tooltip's class line, and the hero in their master class.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_transcend_game.tscn -- --class=knight --level=121
##       --map=int_guildhouse --slot=96 --out=<dir> [--master=grand_paladin] [--res=1280x720] [--touch=1]

var out := ""
var master: StringName = &""
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
		if a.begins_with("--master="):
			master = StringName(a.substr(9))
		if a.begins_with("--res="):
			var wh := a.substr(6).split("x")
			get_window().size = Vector2i(int(wh[0]), int(wh[1]))
		if a == "--touch=1":
			Settings.control_mode = "mobile"
	if out == "":
		out = ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence/screens")
	DirAccess.make_dir_recursive_absolute(out)
	Settings.first_person = false
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 2000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(40)
	p = Game.player as Player
	p.set_first_person(false)
	Game.god_mode = true
	var fam := p.hero.cls.id
	var first: StringName = DataTranscendence.children_of(fam)[0]
	if master == &"":
		master = DataTranscendence.children_of(first)[0]
	var tag := String(fam)
	# the Grand Master in the hall
	var gm := NpcDirectory.find(&"grand_master_edran")
	if gm:
		p.teleport_to(gm.global_position + gm.global_transform.basis.z * 2.6)
		p.face_toward(gm.global_position)
	await _wait(60)
	await _shot("%s_01_grand_master_hall" % tag)
	# the Skills window shows a locked preview of the first advancement
	Game.ui_root.open(&"skills")
	await _wait(10)
	var sw := Game.ui_root.window(&"skills") as SkillsWindow
	sw.tree.bind_preview(p.hero, false, first)
	sw._build_tabs()
	await _wait(10)
	await _shot("%s_02_skills_preview_locked" % tag)
	sw.tree.end_preview()
	Game.ui_root.window(&"skills").close_window()
	await _wait(10)
	# the Class window, stage 0
	Game.ui_root.open(&"transcend")
	await _wait(20)
	await _shot("%s_03_class_first" % tag)
	var tw := Game.ui_root.window(&"transcend") as TranscendWindow
	tw._preview_masters = true
	tw.refresh()
	await _wait(10)
	await _shot("%s_04_class_first_with_master_preview" % tag)
	tw._preview_masters = false
	tw._do_first(first)
	await _wait(20)
	await _shot("%s_05_master_choice" % tag)
	tw._selected = master
	tw.refresh()
	await _wait(10)
	await _shot("%s_06_master_review" % tag)
	tw._do_master(master)
	await _wait(30)
	await _shot("%s_07_class_complete" % tag)
	tw.close_window()
	await _wait(20)
	# the hero, now a master (HUD hidden)
	Game.ui_root.visible = false
	await _wait(30)
	await _shot("%s_08_master_hero" % tag)
	Game.ui_root.visible = true
	# Skills and Talents pages of both advancements
	Game.ui_root.open(&"skills")
	await _wait(10)
	sw = Game.ui_root.window(&"skills") as SkillsWindow
	var pages := p.hero.skill_tree.tree.page_count()
	sw.tree.set_page(pages - 2)
	sw._build_tabs()
	await _wait(10)
	await _shot("%s_09_skills_first_page" % tag)
	sw.tree.set_page(pages - 1)
	sw._build_tabs()
	sw._show(DataTranscendence.info(master).skills[0])
	await _wait(10)
	await _shot("%s_10_skills_master_page" % tag)
	sw.close_window()
	Game.ui_root.open(&"talents")
	await _wait(10)
	var tlw := Game.ui_root.window(&"talents") as TalentsWindow
	tlw.tree.set_page(tlw.hero.talent_tree.tree.page_count() - 1)
	tlw._build_tabs()
	await _wait(10)
	await _shot("%s_11_talents_master_page" % tag)
	tlw.close_window()
	# a class item tooltip: one the hero may wear, one of the sibling master
	var sib: StringName = DataTranscendence.children_of(first).filter(func(x): return x != master)[0]
	var mine := DB.make_item(DataTranscendence.info(master).gear[0], BH.Rarity.ELITE, 125, 3)
	var theirs := DB.make_item(DataTranscendence.info(sib).gear[0], BH.Rarity.ELITE, 125, 4)
	var t1 := Tips.item(mine)
	Game.ui_root.add_child(t1)
	t1.position = Vector2(60, 60)
	var t2 := Tips.item(theirs)
	Game.ui_root.add_child(t2)
	t2.position = Vector2(560, 60)
	await _wait(20)
	await _shot("%s_12_item_class_lines" % tag)
	t1.queue_free()
	t2.queue_free()
	Game.ui_root.open(&"character")
	await _wait(20)
	await _shot("%s_13_character" % tag)
	get_tree().quit()

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("SHOT ", label)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame
