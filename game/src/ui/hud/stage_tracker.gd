class_name StageTracker
extends PanelContainer
## Stage progress on combat maps (bh-007): how many of this map's camps are cleared this visit (a bar), and the map's
## champions (minibosses) — here, defeated, or when they return. Hidden in towns and interiors. Clearing every camp is
## a stage clear; stage clears and champion kills make Olivar's merchants restock.

var _title: Label
var _bar: ProgressBar
var _camps: Label
var _champs: VBoxContainer
var _t := 0.0
var _key := ""

func _init() -> void:
	theme_type_variation = &"GlassPanel"
	custom_minimum_size = Vector2(300, 0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false

func _ready() -> void:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 3)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(v)
	_title = UITheme.label("", 18, UITheme.GOLD, UITheme.title_font())
	v.add_child(_title)
	_bar = ProgressBar.new()
	_bar.custom_minimum_size = Vector2(0, 10)
	_bar.show_percentage = false
	_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color(0.85, 0.62, 0.28)
	fill.set_corner_radius_all(3)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.05, 0.04, 0.04, 0.8)
	bg.set_corner_radius_all(3)
	_bar.add_theme_stylebox_override("fill", fill)
	_bar.add_theme_stylebox_override("background", bg)
	v.add_child(_bar)
	_camps = UITheme.label("", 16, UITheme.TEXT, UITheme.body_font())
	v.add_child(_camps)
	_champs = VBoxContainer.new()
	_champs.add_theme_constant_override("separation", 1)
	_champs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_champs)
	Events.map_loaded.connect(func(_m: StringName) -> void: _t = 0.0)

func _process(delta: float) -> void:
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.5
	var sp := Spawner.current()
	var def := Game.current_map.def if Game.current_map and is_instance_valid(Game.current_map) else null
	var champs := DataMinibosses.on_map(def.id) if def else []
	if sp == null or def == null or def.is_town or (sp.camp_total() == 0 and champs.is_empty()):
		visible = false
		return
	visible = true
	_title.text = "%s · Stage" % def.display_name
	var total := sp.camp_total()
	var done := sp.camps_cleared()
	_bar.max_value = maxi(1, total)
	_bar.value = done
	_camps.text = ("Stage cleared" if sp.stage_done else "Camps cleared %d / %d" % [done, total]) if total > 0 else ""
	_camps.add_theme_color_override("font_color", UITheme.GOOD if sp.stage_done else UITheme.TEXT)
	var lines := []
	for m in champs:
		var state := ""
		var col := UITheme.PARCHMENT
		var alive := sp.minibosses.filter(func(e): return is_instance_valid(e) and e.miniboss.get("id") == m.id and e.alive)
		if not alive.is_empty():
			state = "here"
			col = Color(1.0, 0.62, 0.4)
		elif DataMinibosses.resting(Game.hero, m.id):
			state = "defeated · back in %d min" % ceili(DataMinibosses.seconds_until_back(Game.hero, m.id) / 60.0)
			col = UITheme.GOOD
		else:
			state = "defeated"
			col = UITheme.GOOD
		lines.append([m.name, state, col])
	var key := str(lines)
	if key == _key:
		return
	_key = key
	for c in _champs.get_children():
		c.queue_free()
	for l in lines:
		var lab := UITheme.label("%s — %s" % [l[0], l[1]], 15, l[2], UITheme.body_font())
		lab.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lab.custom_minimum_size = Vector2(270, 0)
		_champs.add_child(lab)
