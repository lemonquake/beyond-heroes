class_name LoadingScreen
extends CanvasLayer
## Map transition screen: fades to black, shows the destination's name, subtitle, level range and a gameplay
## hint over an ornamental frame, then fades back in once the map is built.

const FADE := 0.35

var _veil: ColorRect
var _box: VBoxContainer
var _title: Label
var _subtitle: Label
var _levels: Label
var _hint: Label
var _glow: TextureRect

func _init() -> void:
	layer = 90
	process_mode = Node.PROCESS_MODE_ALWAYS
	_veil = ColorRect.new()
	_veil.color = Color(0.015, 0.012, 0.015, 1.0)
	_veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	_veil.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_veil)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_veil.add_child(center)
	_box = VBoxContainer.new()
	_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_box.add_theme_constant_override("separation", 14)
	_box.custom_minimum_size = Vector2(900, 0)
	center.add_child(_box)
	_glow = TextureRect.new()
	_glow.texture = UITheme.icon("res://assets/ui/emblem/logo_emblem.svg")
	_glow.custom_minimum_size = Vector2(96, 96)
	_glow.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_glow.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_glow.modulate = Color(1, 1, 1, 0.85)
	_box.add_child(_glow)
	_title = UITheme.title("", 54, UITheme.GOLD)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_box.add_child(_title)
	_subtitle = UITheme.label("", 24, UITheme.PARCHMENT, UITheme.body_font())
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_box.add_child(_subtitle)
	var div := TextureRect.new()
	div.texture = UITheme.icon("res://assets/ui/emblem/ornament_divider.svg")
	div.custom_minimum_size = Vector2(520, 28)
	div.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	div.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_box.add_child(div)
	_levels = UITheme.label("", 18, UITheme.TEXT_DIM, UITheme.body_bold())
	_levels.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_box.add_child(_levels)
	_hint = UITheme.label("", 19, UITheme.TEXT, UITheme.body_font())
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint.custom_minimum_size = Vector2(760, 0)
	_box.add_child(_hint)
	_veil.modulate.a = 0.0
	visible = false

func show_for(def: MapDef) -> void:
	if def:
		_title.text = def.display_name
		_subtitle.text = def.subtitle
		_levels.text = ("Safe inside the walls — watch the roads outside" if def.id in [&"olivar", &"wyman_outpost"] else "Safe haven — no enemies") if def.is_town else ("Monster level %d – %d" % [def.level_min, def.level_max]
			if def.level_max > def.level_min else "Monster level %d" % def.level_min)
		_hint.text = def.loading_hint
	visible = true
	_box.modulate.a = 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_veil, "modulate:a", 1.0, FADE)
	tw.tween_property(_box, "modulate:a", 1.0, FADE * 1.6).set_delay(FADE * 0.5)
	await tw.finished

func hide_screen(hold := 0.6) -> void:
	var tw := create_tween()
	tw.tween_interval(hold)
	tw.tween_property(_box, "modulate:a", 0.0, FADE * 0.8)
	tw.tween_property(_veil, "modulate:a", 0.0, FADE * 1.4)
	await tw.finished
	visible = false
