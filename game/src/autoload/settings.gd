extends Node
## Game settings (autoload `Settings`). Persisted to user://settings.cfg and mirrored in save files.

signal changed

const PATH := "user://settings.cfg"

var master_volume := 0.9
var music_volume := 0.6
var sfx_volume := 0.9
var ambience_volume := 0.7
var ui_volume := 0.8
var fullscreen := false
var vsync := true
var screen_shake := 1.0
var damage_numbers := true
var show_enemy_bars := true
var camera_zoom := 1.0
var shadows_quality := 2           # 0 low, 1 medium, 2 high
var fog := true
var ssao := true
var glow := true
var click_to_move := true
var reduced_motion := false
var ui_scale := 1.0

const KEYS := ["master_volume", "music_volume", "sfx_volume", "ambience_volume", "ui_volume", "fullscreen", "vsync",
	"screen_shake", "damage_numbers", "show_enemy_bars", "camera_zoom", "shadows_quality", "fog", "ssao", "glow",
	"click_to_move", "reduced_motion", "ui_scale"]

func _ready() -> void:
	load_file()
	apply()

func to_dict() -> Dictionary:
	var d := {}
	for k in KEYS:
		d[k] = get(k)
	return d

func from_dict(d: Dictionary) -> void:
	for k in KEYS:
		if d.has(k):
			set(k, d[k])
	apply()

func load_file() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return
	for k in KEYS:
		if cfg.has_section_key("settings", k):
			set(k, cfg.get_value("settings", k))

func save_file() -> void:
	var cfg := ConfigFile.new()
	for k in KEYS:
		cfg.set_value("settings", k, get(k))
	cfg.save(PATH)

func apply() -> void:
	_bus("Master", master_volume)
	_bus("Music", music_volume)
	_bus("SFX", sfx_volume)
	_bus("Ambience", ambience_volume)
	_bus("UI", ui_volume)
	if not Engine.is_editor_hint() and DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	changed.emit()

func set_value(key: String, value) -> void:
	set(key, value)
	apply()
	save_file()

func _bus(name: String, v: float) -> void:
	var idx := AudioServer.get_bus_index(name)
	if idx >= 0:
		AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(v, 0.0001)))
		AudioServer.set_bus_mute(idx, v <= 0.001)
