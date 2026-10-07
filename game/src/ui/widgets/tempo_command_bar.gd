class_name TempoCommandBar
extends HBoxContainer
## bh-041: the hero's standing order for its Tempos — Aggro, Defend or Passive (TempoRules.COMMANDS).
## Compact (over the HUD's Tempo frames): one button that steps to the next command on every click. Full (the Tempo
## window): the three commands side by side, the current one lit. Both follow the order however it changes (Y key too).

var compact := false
var _buttons := {}                   # command -> Button

static func make(p_compact: bool) -> TempoCommandBar:
	var b := TempoCommandBar.new()
	b.compact = p_compact
	return b

func _ready() -> void:
	add_theme_constant_override("separation", 6)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if compact:
		var b := _button(&"", 300.0 if not Settings.touch_mode else 320.0)
		b.pressed.connect(func() -> void:
			if Game.hero:
				TempoRules.cycle_command(Game.hero)
				Audio.play_ui(&"ui_click"))
		_buttons[&""] = b
	else:
		add_child(UITheme.label("Command", 18, UITheme.TEXT_DIM, UITheme.body_bold()))
		for c in TempoRules.COMMANDS:
			var cmd: StringName = c
			var b := _button(cmd, 150.0)
			b.toggle_mode = true
			b.pressed.connect(func() -> void:
				if Game.hero:
					TempoRules.set_command(Game.hero, cmd)
					Audio.play_ui(&"ui_click"))
			_buttons[cmd] = b
	Events.tempo_command_changed.connect(func(_c: StringName) -> void: refresh())
	refresh()

func _button(cmd: StringName, w: float) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(w, 46 if Settings.touch_mode else 32)
	b.add_theme_font_size_override("font_size", 16)
	if cmd != &"":
		b.text = TempoRules.command_name(cmd)
	var tip_cmd := cmd
	TooltipLayer.attach(b, func() -> Control:
		var lines := PackedStringArray()
		for c in TempoRules.COMMANDS:
			lines.append("%s%s — %s" % ["▶ " if Game.hero and Game.hero.tempo_command == c else "", TempoRules.command_name(c),
				TempoRules.COMMAND_INFO[c].desc])
		return Tips.text("\n".join(lines) + "\n\n%s steps through them." % Settings.binding_text(&"tempo_command"),
			"Tempo Command" if tip_cmd == &"" else TempoRules.command_name(tip_cmd)))
	add_child(b)
	return b

func refresh() -> void:
	var cur: StringName = TempoRules.clean_command(Game.hero.tempo_command) if Game.hero else &"defend"
	var col := TempoRules.command_color(cur)
	if compact:
		var b: Button = _buttons.get(&"")
		if b:
			b.text = "Tempos: %s  ⟳" % TempoRules.command_name(cur)
			b.add_theme_color_override("font_color", col)
			b.add_theme_color_override("font_hover_color", col.lightened(0.25))
		return
	for c in _buttons:
		var b: Button = _buttons[c]
		var on: bool = c == cur
		b.set_pressed_no_signal(on)
		var cc := TempoRules.command_color(c)
		b.add_theme_color_override("font_color", cc if on else UITheme.TEXT_DIM)
		b.add_theme_color_override("font_pressed_color", cc)
		b.add_theme_color_override("font_hover_color", cc.lightened(0.2))
