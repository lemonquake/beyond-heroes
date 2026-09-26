extends Node
## Game settings (autoload `Settings`). Persisted to user://settings.cfg and mirrored in save files.
## VIDEO, AUDIO, CONTROLS and GAMEPLAY groups; `apply()` pushes everything to the engine, the input map, the audio
## buses and the current world. Key bindings are stored as InputEvent descriptors so they survive saves.

signal changed

const PATH := "user://settings.cfg"

const RESOLUTIONS := [Vector2i(1280, 720), Vector2i(1600, 900), Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(3840, 2160)]
const WINDOW_MODES := ["Windowed", "Borderless", "Fullscreen"]
const QUALITY_NAMES := ["Low", "Medium", "High", "Ultra"]
const AA_NAMES := ["Off", "FXAA", "MSAA 2x", "MSAA 4x", "TAA"]
const AUTO_LOOT_NAMES := ["Off", "Gold only", "Gold + Common", "Gold + Basic", "Gold + Advanced"]

# ---- VIDEO
var resolution := 2                 # index into RESOLUTIONS (windowed size)
var window_mode := 0                # 0 windowed, 1 borderless, 2 exclusive fullscreen
var vsync := true
var fps_limit := 0                  # 0 = unlimited
var shadows_quality := 2            # 0 low (no local shadows) .. 3 ultra
var texture_quality := 2            # anisotropy + mip bias
var effects_quality := 2            # 0 low: no SSAO/volumetric/extra particles .. 3 ultra
var anti_aliasing := 2
var render_scale := 1.0             # 0.5 .. 1.0 (FSR upscaling below 1.0)
# ---- AUDIO
var master_volume := 0.9
var music_volume := 0.6
var sfx_volume := 0.9
var voice_volume := 0.9
var ambience_volume := 0.7
var ui_volume := 0.8
# ---- CONTROLS
var bindings := {}                  # action -> [event descriptor]; empty = defaults (InputSetup.BINDINGS)
var mouse_sensitivity := 1.0        # camera rotation / zoom speed
var guard_toggle := false           # false: hold to guard, true: press to toggle
var attack_hold_repeat := true      # holding attack keeps the combo going
# ---- GAMEPLAY
var damage_numbers := true
var blood := true                   # blood sprays, pools and gore on hits and corpses
var screen_shake := 1.0
var auto_loot_mode := 1             # AUTO_LOOT_NAMES
var show_enemy_bars := true
var loot_labels_always := true      # false: only while Alt is held
var camera_zoom := 1.0
var reduced_motion := false
var ui_scale := 1.0
var show_minimap := true

const KEYS := ["resolution", "window_mode", "vsync", "fps_limit", "shadows_quality", "texture_quality", "effects_quality",
	"anti_aliasing", "render_scale", "master_volume", "music_volume", "sfx_volume", "voice_volume", "ambience_volume",
	"ui_volume", "bindings", "mouse_sensitivity", "guard_toggle", "attack_hold_repeat", "damage_numbers", "blood", "screen_shake",
	"auto_loot_mode", "show_enemy_bars", "loot_labels_always", "camera_zoom", "reduced_motion", "ui_scale", "show_minimap"]

# Derived switches read by the world builders.
var fog: bool:
	get: return true
var glow: bool:
	get: return effects_quality >= 1
var ssao: bool:
	get: return effects_quality >= 2
var auto_loot: bool:
	get: return auto_loot_mode > 0
## Items at or above this rarity are picked up automatically (gold is always taken while auto loot is on).
var auto_loot_rarity: int:
	get: return [BH.RARITY_COUNT, BH.RARITY_COUNT, BH.Rarity.COMMON, BH.Rarity.BASIC, BH.Rarity.ADVANCED][clampi(auto_loot_mode, 0, 4)]
var fullscreen: bool:
	get: return window_mode > 0
const FPS_LIMITS := [0, 30, 60, 120, 144]
var fps_limit_index: int:
	get: return maxi(0, FPS_LIMITS.find(fps_limit))
	set(v): fps_limit = FPS_LIMITS[clampi(v, 0, FPS_LIMITS.size() - 1)]

func _ready() -> void:
	load_file()
	apply()
	apply.call_deferred()  # again once every autoload (audio buses, input map, window) exists

func to_dict() -> Dictionary:
	var d := {}
	for k in KEYS:
		d[k] = get(k)
	return d

func from_dict(d: Dictionary) -> void:
	for k in KEYS:
		if d.has(k):
			set(k, _coerce(k, d[k]))
	# older saves stored a boolean
	if d.has("fullscreen") and not d.has("window_mode"):
		window_mode = 1 if d.fullscreen else 0
	if d.has("shadows_quality"):
		shadows_quality = clampi(int(d.shadows_quality), 0, 3)
	apply()

func _coerce(k: String, v: Variant) -> Variant:
	var cur = get(k)
	match typeof(cur):
		TYPE_INT: return int(v)
		TYPE_FLOAT: return float(v)
		TYPE_BOOL: return bool(v)
		TYPE_DICTIONARY: return v if v is Dictionary else {}
	return v

func load_file() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return
	var d := {}
	for k in KEYS:
		if cfg.has_section_key("settings", k):
			d[k] = cfg.get_value("settings", k)
	if cfg.has_section_key("settings", "fullscreen"):
		d["fullscreen"] = cfg.get_value("settings", "fullscreen")
	for k in d:
		if k in KEYS:
			set(k, _coerce(k, d[k]))

func save_file() -> void:
	var cfg := ConfigFile.new()
	for k in KEYS:
		cfg.set_value("settings", k, get(k))
	cfg.save(PATH)

func set_value(key: String, value) -> void:
	set(key, value)
	apply()
	save_file()

func reset_group(group: String) -> void:
	var defaults := preload("res://src/autoload/settings.gd").new()
	for k in GROUPS.get(group, []):
		set(k, defaults.get(k))
	defaults.free()
	apply()
	save_file()

const GROUPS := {
	"video": ["resolution", "window_mode", "vsync", "fps_limit", "shadows_quality", "texture_quality", "effects_quality", "anti_aliasing", "render_scale"],
	"audio": ["master_volume", "music_volume", "sfx_volume", "voice_volume", "ambience_volume", "ui_volume"],
	"controls": ["bindings", "mouse_sensitivity", "guard_toggle", "attack_hold_repeat"],
	"gameplay": ["damage_numbers", "blood", "screen_shake", "auto_loot_mode", "show_enemy_bars", "loot_labels_always", "camera_zoom",
		"reduced_motion", "ui_scale", "show_minimap"],
}

# ---- Apply ------------------------------------------------------------------------------------------------------

func apply() -> void:
	_apply_audio()
	_apply_bindings()
	if is_inside_tree():
		_apply_video()
		_apply_world()
	changed.emit()

func _apply_audio() -> void:
	_bus("Master", master_volume)
	_bus("Music", music_volume)
	_bus("SFX", sfx_volume)
	_bus("Voice", voice_volume)
	_bus("Ambience", ambience_volume)
	_bus("UI", ui_volume)

func _bus(name: String, v: float) -> void:
	var idx := AudioServer.get_bus_index(name)
	if idx >= 0:
		AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(v, 0.0001)))
		AudioServer.set_bus_mute(idx, v <= 0.001)

func _apply_video() -> void:
	var vp := get_tree().root
	var headless := DisplayServer.get_name() == "headless"
	if not headless and not Engine.is_editor_hint():
		match window_mode:
			0:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
				DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, false)
				var size: Vector2i = RESOLUTIONS[clampi(resolution, 0, RESOLUTIONS.size() - 1)]
				var screen := DisplayServer.screen_get_usable_rect(DisplayServer.window_get_current_screen()).size
				if screen.x > 0:
					size = Vector2i(mini(size.x, screen.x), mini(size.y, screen.y))
				if DisplayServer.window_get_size() != size:
					DisplayServer.window_set_size(size)
			1:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
			2:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = fps_limit
	# anti-aliasing
	vp.msaa_3d = [Viewport.MSAA_DISABLED, Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_4X, Viewport.MSAA_DISABLED][clampi(anti_aliasing, 0, 4)]
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if anti_aliasing == 1 else Viewport.SCREEN_SPACE_AA_DISABLED
	vp.use_taa = anti_aliasing == 4
	# render scale: FSR 1 below native
	vp.scaling_3d_scale = clampf(render_scale, 0.5, 1.0)
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if render_scale < 0.99 else Viewport.SCALING_3D_MODE_BILINEAR
	# textures
	vp.anisotropic_filtering_level = [Viewport.ANISOTROPY_2X, Viewport.ANISOTROPY_4X, Viewport.ANISOTROPY_8X, Viewport.ANISOTROPY_16X][clampi(texture_quality, 0, 3)]
	vp.texture_mipmap_bias = [0.5, 0.25, 0.0, -0.25][clampi(texture_quality, 0, 3)]
	vp.mesh_lod_threshold = [2.5, 1.5, 1.0, 0.5][clampi(effects_quality, 0, 3)]
	# shadows
	var sq := clampi(shadows_quality, 0, 3)
	RenderingServer.directional_shadow_atlas_set_size([2048, 4096, 4096, 8192][sq], true)
	RenderingServer.directional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_LOW,
		RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM, RenderingServer.SHADOW_QUALITY_SOFT_HIGH][sq])
	RenderingServer.positional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_LOW,
		RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM, RenderingServer.SHADOW_QUALITY_SOFT_HIGH][sq])
	vp.positional_shadow_atlas_size = [1024, 2048, 4096, 8192][sq]
	vp.content_scale_factor = clampf(ui_scale, 0.75, 1.5)

## Re-applies world-affecting switches to the loaded map without rebuilding it.
func _apply_world() -> void:
	var map = get_node_or_null("/root/Game")
	if map == null or map.current_map == null or not is_instance_valid(map.current_map):
		return
	var m: MapRoot = map.current_map
	if m.environment and m.environment.environment:
		var env := m.environment.environment
		env.ssao_enabled = ssao
		env.glow_enabled = glow
		if not env.has_meta(&"volumetric_built"):
			env.set_meta(&"volumetric_built", env.volumetric_fog_enabled)
		env.volumetric_fog_enabled = bool(env.get_meta(&"volumetric_built")) and effects_quality >= 2
	if m.sun:
		m.sun.shadow_enabled = shadows_quality > 0
	for l in m.find_children("*", "OmniLight3D", true, false):
		if l.has_meta(&"wants_shadow"):
			l.shadow_enabled = bool(l.get_meta(&"wants_shadow")) and shadows_quality > 1

# ---- Key bindings ------------------------------------------------------------------------------------------------

static func event_to_desc(e: InputEvent) -> Dictionary:
	if e is InputEventKey:
		return {"type": "key", "code": int(e.physical_keycode if e.physical_keycode != 0 else e.keycode)}
	if e is InputEventMouseButton:
		return {"type": "mouse", "button": int(e.button_index)}
	if e is InputEventJoypadButton:
		return {"type": "joy_button", "button": int(e.button_index)}
	if e is InputEventJoypadMotion:
		return {"type": "joy_axis", "axis": int(e.axis), "value": signf(e.axis_value)}
	return {}

static func desc_to_event(d: Dictionary) -> InputEvent:
	match String(d.get("type", "")):
		"key":
			var k := InputEventKey.new()
			k.physical_keycode = int(d.code) as Key
			return k
		"mouse":
			var m := InputEventMouseButton.new()
			m.button_index = int(d.button) as MouseButton
			return m
		"joy_button":
			var j := InputEventJoypadButton.new()
			j.button_index = int(d.button) as JoyButton
			return j
		"joy_axis":
			var a := InputEventJoypadMotion.new()
			a.axis = int(d.axis) as JoyAxis
			a.axis_value = float(d.value)
			return a
	return null

## Rebind: replaces the keyboard/mouse event of `action` (controller events stay). Returns the action that previously
## used this input (it is unbound so no two actions share a key), or &"".
func rebind(action: StringName, ev: InputEvent) -> StringName:
	var desc := event_to_desc(ev)
	var stolen := &""
	for a in InputMap.get_actions():
		if String(a).begins_with("ui_") or a == action:
			continue
		for e in InputMap.action_get_events(a):
			if _same_input(e, ev):
				InputMap.action_erase_event(a, e)
				bindings[String(a)] = _descs(a)
				stolen = a
	for e in InputMap.action_get_events(action):
		if e is InputEventKey or e is InputEventMouseButton:
			InputMap.action_erase_event(action, e)
	InputMap.action_add_event(action, desc_to_event(desc))
	bindings[String(action)] = _descs(action)
	save_file()
	changed.emit()
	return stolen

func reset_bindings() -> void:
	bindings = {}
	InputSetup.install_defaults()
	save_file()
	changed.emit()

static func _same_input(a: InputEvent, b: InputEvent) -> bool:
	var da := event_to_desc(a)
	var db := event_to_desc(b)
	return not da.is_empty() and da == db

func _descs(action: StringName) -> Array:
	var out := []
	for e in InputMap.action_get_events(action):
		var d := event_to_desc(e)
		if not d.is_empty():
			out.append(d)
	return out

func _apply_bindings() -> void:
	if bindings.is_empty():
		return
	for action in bindings:
		if not InputMap.has_action(action):
			continue
		InputMap.action_erase_events(action)
		for d in bindings[action]:
			var e := desc_to_event(d)
			if e:
				InputMap.action_add_event(action, e)

## Display text for the first keyboard/mouse binding of an action ("F", "LMB", "Space").
static func binding_text(action: StringName) -> String:
	if not InputMap.has_action(action):
		return ""
	for e in InputMap.action_get_events(action):
		if e is InputEventKey:
			var code: Key = e.physical_keycode if e.physical_keycode != 0 else e.keycode
			return OS.get_keycode_string(DisplayServer.keyboard_get_label_from_physical(code) if e.physical_keycode != 0 else code)
		if e is InputEventMouseButton:
			return {MOUSE_BUTTON_LEFT: "LMB", MOUSE_BUTTON_RIGHT: "RMB", MOUSE_BUTTON_MIDDLE: "MMB",
				MOUSE_BUTTON_WHEEL_UP: "Wheel Up", MOUSE_BUTTON_WHEEL_DOWN: "Wheel Down"}.get(e.button_index, "Mouse %d" % e.button_index)
	return ""
