extends Node
## bh-005 evidence: a new hero's first minutes and the Tempo hiring screens, captured with the real renderer.
##   Godot --path game --resolution 1920x1080 res://tests/tools/capture_onboarding.tscn -- --class=knight --intro=1 --out=<dir>
## Shots: Tobren's introduction (wake, Tempos, controls, windows), the starter beside the hero, the Field Guide pages,
## the Shrine at a higher grade and its Renowned page, and a renowned spirit fighting in the Ruined Forest.

var args := {}
var out := ""
var main: Node

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", "/tmp/onboarding_shots"))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	await _flow()
	print("CAPTURE DONE")
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(name: String, frames := 12) -> void:
	await _wait(frames)
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
	print("SHOT ", name, " ", img.get_size())

## Advance the running conversation until it shows line `line` of node `node` (typing finished).
func _to(box: DialogueBox, node: String, line := 0) -> void:
	for i in 80:
		var s := box.session
		if s == null or s.finished:
			return
		if s.node_id == node and s.line_index == line:
			break
		box._finish_typing()
		if not s.choices.is_empty() and s.line_index >= s.lines.size() - 1:
			s.choose(0)
		else:
			s.advance()
	await _wait(2)
	box._finish_typing()

func _flow() -> void:
	for i in 900:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(90)
	var ui: UIRoot = Game.ui_root
	var box := ui.dialogue
	var p := Game.player as Player
	var h := Game.hero
	print("TEMPOS ", h.tempos.map(func(t): return t.full_name()))
	# ---- the introduction
	box._finish_typing()
	await _shot("01_intro_wake", 20)
	await _to(box, "wake", 2)
	await _shot("02_intro_wake_choices", 10)
	box.session.choose(0)
	await _to(box, "what", 1)
	await _shot("03_intro_what_tempos", 10)
	await _to(box, "where", 0)
	await _shot("04_intro_where_to_hire", 10)
	await _to(box, "where", 2)
	await _shot("05_intro_renowned", 10)
	await _to(box, "fight", 0)
	await _shot("06_intro_controls", 10)
	await _to(box, "windows", 0)
	await _shot("07_intro_windows", 10)
	await _to(box, "start", 1)
	await _shot("08_intro_end", 10)
	box.session.choose(0)
	await _wait(30)
	# ---- Tobren beside the hero
	await _shot("09_starter_in_town", 60)
	# ---- Field Guide
	var gw := ui.window(&"guide") as GuideWindow
	gw.open_on(0)
	await _shot("10_field_guide_controls", 40)
	gw._tabs.current_tab = 1
	await _shot("11_field_guide_tempos", 30)
	gw._tabs.current_tab = 2
	await _shot("12_field_guide_first_steps", 30)
	gw.close_window()
	await _wait(20)
	# ---- the shrine at Veteran grade
	h.progress.add_xp(XpCurve.total_xp_for_level(8) - h.progress.total_xp)
	h.inventory.gold = 20000
	await _wait(10)
	var cw := ui.window(&"tempo_caller") as TempoCallerWindow
	cw.open_on(&"roster")
	await _shot("13_shrine_veteran_roster", 40)
	cw._tabs.current_tab = 1
	await _shot("14_shrine_renowned", 40)
	var kav := TempoRules.hire_legend(h, &"kavira")
	print("BOUND ", kav.full_name() if kav else "none")
	TempoParty.refresh(h)
	cw._tabs.current_tab = 2
	await _shot("15_shrine_your_tempos", 30)
	cw.close_window()
	await _wait(20)
	ui.open(&"tempos")
	(ui.window(&"tempos") as TempoWindow)._tabs.current_tab = 1
	await _shot("16_tempo_window_renowned", 40)
	ui.window(&"tempos").close_window()
	await _wait(20)
	# ---- a renowned spirit in a fight
	Game.load_map(&"ruined_forest", &"start")
	await _wait(90)
	var at := p.global_position + p.global_transform.basis.z * -7.0
	for i in 5:
		var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"hollow_soldier"), h.progress.level, [],
			at + Vector3(randf_range(-2.5, 2.5), 0, randf_range(-2.5, 2.5)), DataEnemies.DIFFICULTY[1])
		if e:
			e.alert_to(p.global_position)
	Game.god_mode = true
	var shots := 0
	for i in 600:
		await get_tree().process_frame
		var k := TempoParty.actor_for(kav.uid) if kav else null
		if k and k.last_skill != &"" and shots == 0 and i > 60:
			shots += 1
			await _shot("17_renowned_fighting", 2)
		if i == 420 and shots == 0:
			await _shot("17_renowned_fighting", 2)
	for t in TempoParty.actors():
		print("LOG ", t.data.full_name(), " ", t.debug_log)
