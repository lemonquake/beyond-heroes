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
	frame.custom_minimum_size = Vector2(420, 620)
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
	_box.add_child(_sub)

func _rebuild() -> void:
	for b in _buttons:
		b.queue_free()
	_buttons.clear()
	var items: Array
	if _death:
		items = [["Respawn", _respawn, &"PrimaryButton"]]
		var cp := Game.checkpoint_name()
		if cp != "":
			items.append(["Wake at %s" % cp, _respawn_checkpoint, &""])
		items.append(["Main Menu", _main_menu, &""])
	else:
		items = [["Resume", close, &"PrimaryButton"], ["Settings", _settings, &""], ["Save Game", _save, &""],
			["Main Menu", _main_menu, &""], ["Quit Game", _quit, &""]]
	for it in items:
		var b := UIWindow.button(it[0], it[1], it[2], 280.0)
		b.custom_minimum_size.y = 58
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		_box.add_child(b)
		_buttons.append(b)
	_buttons[0].grab_focus.call_deferred()

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
	_sub.text = "%s · Level %d %s · %s" % [h.hero_name, h.progress.level, h.cls.display_name, _time(h.play_time)] if h else ""
	_rebuild()
	visible = true
	get_tree().paused = true
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.15)

func show_death() -> void:
	_death = true
	_title.text = "You Have Fallen"
	_title.add_theme_color_override("font_color", Color(0.9, 0.25, 0.2))
	var lost := int(Game.hero.inventory.gold * 0.05) if Game.hero else 0
	var cp := Game.checkpoint_name()
	_sub.text = "Respawn at this area's entrance%s%s" % [
		(",\nor wake at %s." % cp) if cp != "" else ".\nRest at a camp bonfire to set a checkpoint.",
		("\nYou will lose %d gold." % lost) if lost > 0 else ""]
	_rebuild()
	visible = true
	modulate.a = 0.0
	var tw := create_tween()
	tw.tween_interval(1.4)
	tw.tween_property(self, "modulate:a", 1.0, 0.8)

func close() -> void:
	visible = false
	get_tree().paused = false

func _respawn() -> void:
	visible = false
	Game.respawn_player()

func _respawn_checkpoint() -> void:
	visible = false
	Game.respawn_player(true)

func _settings() -> void:
	close()
	Game.ui_root.open(&"settings")

func _save() -> void:
	if Game.save_now():
		_sub.text = "Game saved."

func _main_menu() -> void:
	Game.ui_root.ask("Return to Main Menu", "Your progress is saved automatically. Return to the main menu?", func() -> void:
		close()
		Game.return_to_menu(), "Main Menu")

func _quit() -> void:
	Game.ui_root.ask("Quit Game", "Save and quit Beyond Heroes?", func() -> void:
		Game.save_now()
		get_tree().quit(), "Quit", true)

static func _time(t: float) -> String:
	var m := int(t) / 60
	return "%dh %02dm played" % [m / 60, m % 60]
