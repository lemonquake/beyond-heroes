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
## Auto-loot filter (the on/off switch is `auto_loot_enabled`, the HUD checkbox beside the HP orb). Gold is always
## collected on contact.
const AUTO_LOOT_NAMES := ["All items", "Equipment: Common and better", "Equipment: Basic and better", "Equipment: Advanced and better", "Equipment: Elite and better"]

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
var combat_music := true            # the battle theme takes over while monsters are fighting the hero
# ---- CONTROLS
var bindings := {}                  # action -> [event descriptor]; empty = defaults (InputSetup.BINDINGS)
var mouse_sensitivity := 1.0        # camera rotation / zoom speed
var guard_toggle := false           # false: hold to guard, true: press to toggle
var attack_hold_repeat := true      # holding attack keeps the combo going
# ---- GAMEPLAY
var damage_numbers := true
var blood := true                   # blood sprays, pools and gore on hits and corpses
var screen_shake := 1.0
var auto_loot_enabled := false      # HUD checkbox: walk over matching drops to pick them up
var auto_loot_mode := 0             # AUTO_LOOT_NAMES (which drops auto-loot takes)
var auto_loot_rules := {}           # AutoLootRules: category and advanced filters, saved per hero
var show_enemy_bars := true
var loot_labels_always := true      # false: only while Alt is held
var camera_zoom := 1.0
var first_person := false           # bh-030: play in first-person view (V toggles)
var fp_fov := 80.0                  # bh-030: first-person field of view (degrees)
var reduced_motion := false
var ui_scale := 1.0
var ui_auto := true                 # bh-032: windows smaller than 1920x1080 enlarge the interface so text stays readable
var show_minimap := true
var minimap_zoom := 1                # bh-015: 0 close, 1 normal, 2 wide (MiniMap.ZOOMS)
# ---- PLATFORM (bh-008): asked once on the first launch, changeable in Settings > Controls
var control_mode := ""              # "" not chosen yet, "pc" keyboard + mouse, "mobile" touch controls
var touch_opacity := 0.85           # on-screen controls
var touch_size := 1.0               # scale of the on-screen buttons and stick
var touch_auto_aim := true          # attacks and tapped skills turn toward the nearest enemy
var touch_fixed_stick := false      # false: the stick appears where the left thumb lands
# ---- EFFICIENCY (bh-009): on with Mobile. Low-end phones: the OpenGL renderer, a light budget, lighter shaders and maps,
# sleeping far actors, 30 fps. Read by the map builders (applies from the next map load) and by `Perf`.
var efficiency_mode := false

const KEYS := ["resolution", "window_mode", "vsync", "fps_limit", "shadows_quality", "texture_quality", "effects_quality",
	"anti_aliasing", "render_scale", "master_volume", "music_volume", "sfx_volume", "voice_volume", "ambience_volume",
	"ui_volume", "combat_music", "bindings", "mouse_sensitivity", "guard_toggle", "attack_hold_repeat", "damage_numbers", "blood", "screen_shake",
	"auto_loot_enabled", "auto_loot_mode", "auto_loot_rules", "show_enemy_bars", "loot_labels_always", "camera_zoom", "first_person", "fp_fov", "reduced_motion", "ui_scale", "ui_auto", "show_minimap",
	"minimap_zoom", "control_mode", "touch_opacity", "touch_size", "touch_auto_aim", "touch_fixed_stick", "efficiency_mode"]

# Derived switches read by the world builders.
var fog: bool:
	get: return true
var glow: bool:
	get: return effects_quality >= 1 and not efficiency_mode
var ssao: bool:
	get: return effects_quality >= 2 and not efficiency_mode
## Total efficiency (Mobile): every system that has a cheaper path takes it.
var lite: bool:
	get: return efficiency_mode
var auto_loot: bool:
	get: return auto_loot_enabled
## Items at or above this rarity are picked up automatically while auto-loot is on.
var auto_loot_rarity: int:
	get: return [BH.Rarity.BEGINNER, BH.Rarity.COMMON, BH.Rarity.BASIC, BH.Rarity.ADVANCED, BH.Rarity.ELITE][clampi(auto_loot_mode, 0, 4)]
var fullscreen: bool:
	get: return window_mode > 0
## Touch play: on-screen stick and buttons, auto-aim, long-press for right-click.
var touch_mode: bool:
	get: return control_mode == "mobile"
## Running on a phone or tablet (the export, not the chosen control mode).
static func is_mobile_device() -> bool:
	return OS.has_feature("mobile") or OS.has_feature("android") or OS.has_feature("ios")
const FPS_LIMITS := [0, 30, 60, 120, 144]
var fps_limit_index: int:
	get: return maxi(0, FPS_LIMITS.find(fps_limit))
	set(v): fps_limit = FPS_LIMITS[clampi(v, 0, FPS_LIMITS.size() - 1)]

func _ready() -> void:
	load_file()
	get_window().size_changed.connect(_on_window_resized)
	apply()
	apply.call_deferred()  # again once every autoload (audio buses, input map, window) exists

func to_dict() -> Dictionary:
	var d := {}
	for k in KEYS:
		d[k] = get(k)
	return d

## Settings that belong to the device, not to the hero (bh-009): a save carries its settings along, but loading it on
## a phone must not bring back a desktop's shadows and uncapped frame rate (or turn a PC into touch play).
const DEVICE_KEYS := ["resolution", "window_mode", "vsync", "fps_limit", "shadows_quality", "texture_quality", "effects_quality",
	"anti_aliasing", "render_scale", "efficiency_mode", "ui_scale", "ui_auto", "control_mode", "touch_opacity", "touch_size", "touch_auto_aim",
	"touch_fixed_stick"]

func from_dict(d: Dictionary) -> void:
	for k in KEYS:
		if d.has(k) and not k in DEVICE_KEYS:
			set(k, _coerce(k, d[k]))
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
		if is_mobile_device():
			_mobile_defaults()
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
	# a phone that saved its settings before efficiency mode existed (or a PC that picked Mobile): switch it on once
	if not d.has("efficiency_mode") and (is_mobile_device() or control_mode == "mobile"):
		_efficiency_preset()

## First launch on a phone or tablet: settings a mobile GPU and a small screen are comfortable with.
func _mobile_defaults() -> void:
	_efficiency_preset()
	ui_scale = 1.25
	auto_loot_enabled = true
	auto_loot_mode = 1

## The Mobile video preset: no shadows, no post effects, no anti-aliasing, 3D drawn at 70 % and scaled up, 30 fps.
func _efficiency_preset() -> void:
	efficiency_mode = true
	shadows_quality = 0
	texture_quality = 0
	effects_quality = 0
	anti_aliasing = 0
	render_scale = 0.7
	fps_limit = 30

## Back to the desktop defaults when leaving efficiency mode.
func _desktop_preset() -> void:
	efficiency_mode = false
	shadows_quality = 2
	texture_quality = 2
	effects_quality = 2
	anti_aliasing = 2
	render_scale = 1.0
	fps_limit = 0

## Switch between keyboard + mouse and touch play (the first-launch question and Settings > Controls). Mobile turns
## on total efficiency; PC turns it off again (a phone always keeps it: its GPU is the reason it exists).
func set_control_mode(mode: String) -> void:
	control_mode = mode
	if mode == "mobile":
		if not efficiency_mode:
			_efficiency_preset()
		if ui_scale < 1.2 and is_mobile_device():
			ui_scale = 1.25
	elif efficiency_mode and not is_mobile_device():
		_desktop_preset()
	apply()
	save_file()

## Settings > Video > Efficiency Mode.
func set_efficiency(on: bool) -> void:
	if on == efficiency_mode:
		return
	if on:
		_efficiency_preset()
	else:
		_desktop_preset()
	apply()
	save_file()
	changed.emit()

func save_file() -> void:
	var cfg := ConfigFile.new()
	for k in KEYS:
		cfg.set_value("settings", k, get(k))
	cfg.save(PATH)

func set_value(key: String, value) -> void:
	if key == "auto_loot_mode":
		auto_loot_rules.erase("min_rarity")
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
	"video": ["resolution", "window_mode", "vsync", "fps_limit", "shadows_quality", "texture_quality", "effects_quality", "anti_aliasing", "render_scale",
		"efficiency_mode"],
	"audio": ["master_volume", "music_volume", "sfx_volume", "voice_volume", "ambience_volume", "ui_volume", "combat_music"],
	"controls": ["bindings", "mouse_sensitivity", "guard_toggle", "attack_hold_repeat", "touch_opacity", "touch_size", "touch_auto_aim",
		"touch_fixed_stick"],
	"gameplay": ["damage_numbers", "blood", "screen_shake", "auto_loot_enabled", "auto_loot_mode", "auto_loot_rules", "show_enemy_bars", "loot_labels_always", "camera_zoom",
		"reduced_motion", "ui_scale", "show_minimap", "minimap_zoom"],
}

# ---- Apply ------------------------------------------------------------------------------------------------------

func apply() -> void:
	_apply_audio()
	_apply_bindings()
	_apply_touch_input()
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
	if not headless and not Engine.is_editor_hint() and not is_mobile_device():
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
	if not headless and not Engine.is_editor_hint():
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = fps_limit
	# anti-aliasing
	vp.msaa_3d = [Viewport.MSAA_DISABLED, Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_4X, Viewport.MSAA_DISABLED][clampi(anti_aliasing, 0, 4)]
	if RenderingServer.get_current_rendering_method() != "gl_compatibility":   # no FXAA in the OpenGL fallback
		vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if anti_aliasing == 1 else Viewport.SCREEN_SPACE_AA_DISABLED
	vp.use_taa = anti_aliasing == 4
	# render scale: FSR 1 below native
	vp.scaling_3d_scale = clampf(render_scale, 0.5, 1.0)
	# FSR exists only in the desktop (Forward+) renderer; phones use the Mobile renderer and plain bilinear upscaling
	var fsr_ok := RenderingServer.get_current_rendering_method() == "forward_plus"
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if render_scale < 0.99 and fsr_ok else Viewport.SCALING_3D_MODE_BILINEAR
	# textures
	vp.anisotropic_filtering_level = [Viewport.ANISOTROPY_2X, Viewport.ANISOTROPY_4X, Viewport.ANISOTROPY_8X, Viewport.ANISOTROPY_16X][clampi(texture_quality, 0, 3)]
	vp.texture_mipmap_bias = [0.5, 0.25, 0.0, -0.25][clampi(texture_quality, 0, 3)]
	vp.mesh_lod_threshold = [2.5, 1.5, 1.0, 0.5][clampi(effects_quality, 0, 3)]
	if efficiency_mode:
		# bh-009: coarser mesh LODs sooner, and a slow frame catches up with at most 3 physics steps (a phone that
		# falls behind must not spend the next frame catching up, which makes the one after slower still)
		vp.mesh_lod_threshold = 4.0
		vp.texture_mipmap_bias = 0.75
	Engine.max_physics_steps_per_frame = 3 if efficiency_mode else 6
	# shadows
	var sq := clampi(shadows_quality, 0, 3)
	RenderingServer.directional_shadow_atlas_set_size([2048, 4096, 4096, 8192][sq], true)
	RenderingServer.directional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_LOW,
		RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM, RenderingServer.SHADOW_QUALITY_SOFT_HIGH][sq])
	RenderingServer.positional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_LOW,
		RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM, RenderingServer.SHADOW_QUALITY_SOFT_HIGH][sq])
	vp.positional_shadow_atlas_size = [1024, 2048, 4096, 8192][sq]
	vp.content_scale_factor = effective_ui_scale()

## bh-032: the scale the interface is drawn at. Interface Scale is a multiplier on an automatic one. The interface is drawn for a
## 1920x1080 window; in a smaller window the engine shrinks every pixel with it, so at 1280x720 the 15-pixel quest, party and
## map labels came out about 10 pixels tall. The automatic part enlarges the interface as the window shrinks (up to the 1.5 the
## Interface Scale slider already allowed) so text keeps about the size it has at 1080p. A phone screen is read from close but is
## physically small, so touch play keeps its own scale (see TouchText for its labels).
func effective_ui_scale(window_size := Vector2i.ZERO) -> float:
	if window_size == Vector2i.ZERO:
		var w := get_window()
		window_size = w.size if w else Vector2i(1920, 1080)
	if not ui_auto or _fixed_layouts > 0:
		return clampf(ui_scale, 0.75, 1.5)
	var native := minf(float(window_size.x) / 1920.0, float(window_size.y) / 1080.0)
	var auto := clampf(1.0 / maxf(native, 0.01), 1.0, 1.5)
	if touch_mode or is_mobile_device():
		auto = 1.0       # touch layouts are drawn for the 1.25 phone scale (a larger one makes the stick and buttons crowd the HUD); TouchText enlarges small labels instead
	return clampf(ui_scale * auto, 0.75, 1.5)

var _fixed_layouts := 0

## Full-screen menus placed in pixels for a 1920x1080 canvas (hero choice and creator) call this with true while they are on screen
## and false when they leave: they keep the engine's own scaling, as before the automatic interface scale, instead of
## overflowing a canvas that is now smaller.
func hold_design_scale(on: bool) -> void:
	_fixed_layouts = maxi(0, _fixed_layouts + (1 if on else -1))
	_on_window_resized()

func _on_window_resized() -> void:
	if is_inside_tree():
		get_viewport().content_scale_factor = effective_ui_scale()

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

const MODIFIER_KEYS := [KEY_ALT, KEY_CTRL, KEY_SHIFT, KEY_META]

static func event_to_desc(e: InputEvent) -> Dictionary:
	if e is InputEventKey:
		var d := {"type": "key", "code": int(e.physical_keycode if e.physical_keycode != 0 else e.keycode)}
		# bh-030: combinations (Alt+Q). A plain key stays {type, code} so older settings files read the same.
		for m in [["alt", e.alt_pressed], ["ctrl", e.ctrl_pressed], ["shift", e.shift_pressed]]:
			if m[1] and not MODIFIER_KEYS.has(d.code):
				d[m[0]] = true
		return d
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
			k.alt_pressed = bool(d.get("alt", false))
			k.ctrl_pressed = bool(d.get("ctrl", false))
			k.shift_pressed = bool(d.get("shift", false))
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

## In touch play a tap is also reported as a left click (emulated mouse). The on-screen buttons press the gameplay
## actions themselves, so the mouse buttons are taken off them: a thumb on the stick must not swing the sword.
const TOUCH_STRIPPED := [&"primary", &"secondary", &"zoom_in", &"zoom_out"]
var _stripped := {}                 # action -> [InputEventMouseButton] removed while touch play is on

func _apply_touch_input() -> void:
	if touch_mode:
		for a in TOUCH_STRIPPED:
			if not InputMap.has_action(a):
				continue
			for e in InputMap.action_get_events(a):
				if e is InputEventMouseButton:
					InputMap.action_erase_event(a, e)
					if not _stripped.has(a):
						_stripped[a] = []
					_stripped[a].append(e)
	elif not _stripped.is_empty():
		for a in _stripped:
			for e in _stripped[a]:
				if InputMap.has_action(a) and not InputMap.action_has_event(a, e):
					InputMap.action_add_event(a, e)
		_stripped.clear()

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
			var mods := ("Ctrl+" if e.ctrl_pressed else "") + ("Alt+" if e.alt_pressed else "") + ("Shift+" if e.shift_pressed and code != KEY_SHIFT else "")
			return mods + OS.get_keycode_string(DisplayServer.keyboard_get_label_from_physical(code) if e.physical_keycode != 0 and DisplayServer.get_name() != "headless" else code)
		if e is InputEventMouseButton:
			return {MOUSE_BUTTON_LEFT: "LMB", MOUSE_BUTTON_RIGHT: "RMB", MOUSE_BUTTON_MIDDLE: "MMB",
				MOUSE_BUTTON_WHEEL_UP: "Wheel Up", MOUSE_BUTTON_WHEEL_DOWN: "Wheel Down"}.get(e.button_index, "Mouse %d" % e.button_index)
	return ""
