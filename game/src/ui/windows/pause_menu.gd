class_name PauseMenu
extends Control
## Pause (Escape): Resume, Settings, Save Game, Main Menu, Quit. Also the death screen: Respawn (costs 5% gold).

var _box: VBoxContainer
var _title: Label
var _sub: Label
var _death := false
var _buttons: Array[Button] = []

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0.0, 0.0, 0.0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var vig := TextureRect.new()
	vig.texture = UIArt.tex("hud/vignette_dark.png")
	vig.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vig)
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(c)
	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIArt.style("menu/menu_frame.png"))
	frame.custom_minimum_size = Vector2(420, 690)
	c.add_child(frame)
	_box = VBoxContainer.new()
	_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_box.add_theme_constant_override("separation", 12)
	frame.add_child(_box)
	_title = UITheme.title("Paused", 38, UITheme.GOLD)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_box.add_child(_title)
	_sub = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	# bh-033: wrap inside the frame's art border (a long line used to run under the ornaments)
	_sub.custom_minimum_size = Vector2(320, 0)
	_sub.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_box.add_child(_sub)

func _rebuild() -> void:
	for b in _buttons:
		b.queue_free()
	_buttons.clear()
	var items: Array
	if _death:
		items = [["Respawn", _respawn, &"PrimaryButton"]]
		if Net.is_client() and not Net.official_room:
			items.append(["Respawn beside %s" % Net.host_name(), _respawn_beside_host, &""])
		var cp := Game.checkpoint_name()
		if cp != "":
			items.append(["Wake at %s" % cp, _respawn_checkpoint, &""])
		items.append(["Main Menu", _main_menu, &""])
	else:
		items = [["Resume", close, &"PrimaryButton"], ["Multiplayer", _multiplayer, &""], ["Settings", _settings, &""], ["Save Game", _save, &""],
			["Main Menu", _main_menu, &""], ["Quit Game", _quit, &""]]
	for it in items:
		var b := UIWindow.button(it[0], it[1], it[2], 280.0)
		b.custom_minimum_size.y = 58
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		_box.add_child(b)
		_buttons.append(b)
	_buttons[0].grab_focus.call_deferred()

func is_death() -> bool:
	return _death

func toggle() -> void:
	if visible:
		close()
	else:
		open()

func open() -> void:
	_death = false
	_title.text = "Paused"
	_title.add_theme_color_override("font_color", UITheme.GOLD)
	var h := Game.hero
	_sub.text = "%s · Level %d %s · %s" % [h.hero_name, h.progress.level, ClassTranscendence.current_class_name(h), _time(h.play_time)] if h else ""
	if Settings.touch_mode:
		_sub.text += "\nPress Back again to resume."
	_rebuild()
	visible = true
	get_tree().paused = not Net.is_active()     # the world keeps running for the others (bh-008)
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.15)

func show_death() -> void:
	_death = true
	_title.text = "You Have Fallen"
	_title.add_theme_color_override("font_color", Color(0.9, 0.25, 0.2))
	var lost := int(Game.hero.inventory.gold * 0.05) if Game.hero else 0
	# bh-040: in the Descent a fall also costs part of the current level's experience
	var cost := Game._fall_cost_text(lost, Descent.death_xp_loss(Game.hero)).replace("You lost", "You will lose")
	var cp := Game.checkpoint_name()
	_sub.text = "Respawn at this area's entrance%s%s" % [
		(",\nor wake at %s." % cp) if cp != "" else ".\nRest at a camp bonfire to set a checkpoint.",
		("\n" + cost) if cost != "" else ""]
	if Net.is_active() and Net.player_count() > 1:
		_sub.text = "A friend can revive you right here: they stand beside you and press Interact.\n" + _sub.text
	# bh-033: fallen to a boss — what happened and what to try next
	for e in get_tree().get_nodes_in_group(&"enemy"):
		var en := e as Enemy
		if en and en.alive and en.is_boss and DataBossGuides.wipe_line(en.def.id) != "":
			_sub.text = DataBossGuides.wipe_line(en.def.id) + "\n\n" + _sub.text
			break
	_rebuild()
	visible = true
	modulate.a = 0.0
	var tw := create_tween()
	tw.tween_interval(1.4)
	tw.tween_property(self, "modulate:a", 1.0, 0.8)

func close() -> void:
	visible = false
	get_tree().paused = Official.active and not Official.connected

func _respawn() -> void:
	visible = false
	Game.respawn_player()

## In someone else's world: get up at the entrance, then regroup at the host's side (bh-011).
func _respawn_beside_host() -> void:
	visible = false
	await Game.respawn_player()
	Net.regroup()

func _respawn_checkpoint() -> void:
	visible = false
	Game.respawn_player(true)

func _multiplayer() -> void:
	close()
	Game.ui_root.open(&"multiplayer")

func _settings() -> void:
	close()
	Game.ui_root.open(&"settings")

func _save() -> void:
	if Official.active:
		_sub.text = "Saving to the official server…"
		_sub.text = "Progress saved on the official server." if await Official.flush() else "The server has not confirmed your latest progress."
		return
	if Game.save_now():
		_sub.text = "Game saved."

func _main_menu() -> void:
	Game.ui_root.ask("Return to Main Menu", "Your progress is saved automatically. Return to the main menu?", func() -> void:
		close()
		Game.return_to_menu(), "Main Menu")

func _quit() -> void:
	if Official.active:
		Game.ui_root.ask("Quit Game", "Save your official character on the server and close Beyond Heroes?", func() -> void:
			get_tree().current_scene.call("_quit_safely"), "Save and Quit")
		return
	# three ways out of the question: save and quit, quit without saving, or stay (Cancel / Back)
	var extra := UIWindow.button("Quit Without Saving", func() -> void:
		Game.ui_root.confirm.cancel()
		get_tree().quit(), &"", 300.0)
	extra.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	extra.add_theme_color_override("font_color", Color(1.0, 0.6, 0.5))
	Game.ui_root.confirm.ask("Quit Game", "Save your progress and close Beyond Heroes?", func() -> void:
		Game.save_now()
		get_tree().quit(), "Save and Quit", false, extra)

static func _time(t: float) -> String:
	var m := int(t) / 60
	return "%dh %02dm played" % [m / 60, m % 60]
