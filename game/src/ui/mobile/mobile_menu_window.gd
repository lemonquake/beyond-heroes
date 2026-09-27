class_name MobileMenuWindow
extends UIWindow
## Touch play's hub (the Menu button): every window a keyboard reaches with a hotkey, as big buttons, plus what the
## keyboard HUD shows beside the HP orb (Auto-Loot, carried load, the open Town Portal) and Save Game.

const ENTRIES := [
	["inventory", "Inventory", "ui", "shop"],
	["character", "Character", "classes", "knight"],
	["skills", "Skills", "attributes", "intelligence"],
	["talents", "Talents", "attributes", "wisdom"],
	["tempos", "Tempos", "classes", "tempo_swordsman"],
	["world_map", "World Map", "ui", "map"],
	["guide", "Field Guide", "ui", "quest"],
	["multiplayer", "Multiplayer", "ui", "teleport"],
	["settings", "Settings", "ui", "settings"],
]

var _auto_loot: CheckButton
var _load: Label
var _portal_row: HBoxContainer
var _portal_label: Label

func _init() -> void:
	super._init("Menu", Vector2(1100, 700))
	modal = true

func _build() -> void:
	var grid := GridContainer.new()
	grid.columns = 5
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 16)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	body.add_child(grid)
	for e in ENTRIES:
		grid.add_child(_tile(e[0], e[1], e[2], e[3]))
	body.add_child(HSeparator.new())
	var row := hbox(24)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(row)
	_auto_loot = CheckButton.new()
	_auto_loot.text = "Auto-Loot"
	_auto_loot.focus_mode = Control.FOCUS_NONE
	_auto_loot.add_theme_font_size_override("font_size", 24)
	_auto_loot.toggled.connect(func(on: bool) -> void:
		if on != Settings.auto_loot_enabled:
			Settings.set_value("auto_loot_enabled", on))
	row.add_child(_auto_loot)
	_load = UITheme.label("", 22, UITheme.PARCHMENT, UITheme.body_font())
	row.add_child(_load)
	var save := button("Save Game", func() -> void:
		Game.save_now(), &"", 220.0)
	save.custom_minimum_size.y = 64
	row.add_child(save)
	_portal_row = hbox(16)
	_portal_row.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(_portal_row)
	_portal_label = UITheme.label("", 21, Color(0.8, 0.65, 1.0), UITheme.body_bold())
	_portal_row.add_child(_portal_label)
	var dispel := button("Dispel Portal", func() -> void:
		TownPortal.dispel()
		refresh(), &"", 220.0)
	dispel.custom_minimum_size.y = 56
	_portal_row.add_child(dispel)

func _tile(id: String, text: String, cat: String, icon_id: String) -> Button:
	var b := Button.new()
	b.text = text
	b.icon = UIArt.icon(cat, icon_id)
	b.expand_icon = true
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	b.custom_minimum_size = Vector2(186, 170)
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 24)
	b.add_theme_constant_override("icon_max_width", 84)
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		close_window()
		if Game.ui_root:
			Game.ui_root.open(StringName(id)))
	return b

func refresh() -> void:
	var p := Game.player as Player
	_auto_loot.set_pressed_no_signal(Settings.auto_loot_enabled)
	if p and p.stats:
		_load.text = "Load %.1f / %.0f" % [p.stats.get_stat(&"carry_weight"), p.stats.get_stat(&"carry_capacity")]
	var tp: Dictionary = Game.hero.town_portal if Game.hero else {}
	_portal_row.visible = not tp.is_empty()
	if _portal_row.visible:
		var def := DB.map_def(StringName(tp.get("map", "")))
		_portal_label.text = "Town Portal open in %s" % (def.display_name if def else "the wilds")
