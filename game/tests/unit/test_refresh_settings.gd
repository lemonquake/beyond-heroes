extends TestCase
## Device frame-limit choices survive quality presets and legacy settings migration. No player settings are written.

class DeviceSettings extends "res://src/autoload/settings.gd":
	func apply() -> void:
		pass
	func save_file() -> void:
		pass

func _init() -> void:
	strict = true

func test_safe_mobile_default_and_explicit_high_refresh() -> void:
	var s := DeviceSettings.new()
	s._mobile_defaults()
	eq(s.fps_limit, 60, "a fresh mobile install targets responsive 60 FPS with light rendering")
	eq(s.effects_quality, 0, "the default still uses the light rendering preset")
	s.set_value("fps_limit", 120)
	s.set_efficiency(false)
	eq(s.fps_limit, 120, "leaving efficiency mode keeps the selected cap")
	s.set_efficiency(true)
	eq(s.fps_limit, 120, "enabling efficiency mode keeps the selected cap")
	s.set_control_mode("pc")
	s.set_control_mode("mobile")
	eq(s.fps_limit, 120, "switching control mode also keeps the selected cap")
	for rate in [0, 30, 60, 90, 120, 144, 165, 240]:
		ok(s.FPS_LIMITS.has(rate), "%d FPS remains selectable" % rate)
		s.fps_limit_index = s.FPS_LIMITS.find(rate)
		eq(s.fps_limit, rate, "option selects its numeric cap")
	s.free()
	done()

func test_first_touch_choice_uses_safe_default() -> void:
	var s := DeviceSettings.new()
	s.set_control_mode("mobile")
	eq(s.fps_limit, 60, "first touch choice gets the 60 FPS default when no cap was chosen")
	s.free()
	s = DeviceSettings.new()
	s.set_value("fps_limit", 144)
	s.set_control_mode("mobile")
	eq(s.fps_limit, 144, "an explicit cap chosen before touch mode survives")
	s.free()
	done()

func test_legacy_file_preserves_numeric_frame_limit() -> void:
	const TEMP := "user://refresh-settings-unit.cfg"
	var cfg := ConfigFile.new()
	cfg.set_value("settings", "fps_limit", 120)
	cfg.set_value("settings", "control_mode", "mobile")
	eq(cfg.save(TEMP), OK, "isolated legacy fixture is saved")
	var s := DeviceSettings.new()
	s.load_file(TEMP)
	ok(s.efficiency_mode, "legacy touch settings acquire the light quality preset")
	eq(s.fps_limit, 120, "migration preserves 120 as a value rather than an option index")
	s.free()
	cfg.set_value("settings", "fps_limit", 75)
	cfg.set_value("settings", "efficiency_mode", true)
	cfg.save(TEMP)
	s = DeviceSettings.new()
	s.load_file(TEMP)
	eq(s.fps_limit, 75, "custom numeric caps survive a normal settings load")
	s.free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEMP))
	done()

func test_awake_visual_leaving_crowd_restores_stride() -> void:
	var saved_lite := Settings.efficiency_mode
	Settings.efficiency_mode = false
	var holder := Node3D.new()
	host.add_child(holder)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 2, 8)
	holder.add_child(cam)
	cam.look_at(Vector3(0, 1, 0))
	var v := CharacterVisual.new()
	holder.add_child(v)
	v.tree = AnimationTree.new()
	v.add_child(v.tree)
	v.ally_lod = true
	v.set_anim_stride(3)
	eq(v.anim_stride, 3, "fixture starts at a coarser stride")
	Perf._sleep_animations(cam, Vector3.ZERO)
	ok(v._anim_awake, "the companion is on screen")
	eq(v.anim_stride, 1, "awake companion returns to full rate outside efficiency mode")
	v.crowd_lod = true
	v.ally_lod = false
	v.set_anim_stride(3)
	Perf._sleep_animations(cam, Vector3.ZERO)
	eq(v.anim_stride, 1, "a small eligible crowd also returns to full rate")
	holder.free()
	Settings.efficiency_mode = saved_lite
	done()

func test_native_refresh_is_optional_on_desktop() -> void:
	if not OS.has_feature("android"):
		ok(not Settings.AndroidRefresh.request(120), "desktop has no Android native request")
	done()

func test_binding_labels_on_portable_and_desktop_backends() -> void:
	const ACTION := &"refresh_settings_binding_fixture"
	InputMap.add_action(ACTION)
	var key := InputEventKey.new()
	key.physical_keycode = KEY_W
	key.ctrl_pressed = true
	key.alt_pressed = true
	key.shift_pressed = true
	InputMap.action_add_event(ACTION, key)
	var physical := Settings.binding_text(ACTION)
	ok(physical.begins_with("Ctrl+Alt+Shift+"), "physical bindings retain modifiers on every backend")
	ok(physical.length() > "Ctrl+Alt+Shift+".length(), "a physical binding always has a readable key label")
	if Settings.is_mobile_device() or DisplayServer.get_name() == "headless":
		eq(physical, "Ctrl+Alt+Shift+W", "backends without layout translation use the portable physical-position label")
	InputMap.action_erase_events(ACTION)
	key = InputEventKey.new()
	key.keycode = KEY_F
	key.ctrl_pressed = true
	InputMap.action_add_event(ACTION, key)
	eq(Settings.binding_text(ACTION), "Ctrl+F", "logical bindings retain their named key")
	InputMap.action_erase_events(ACTION)
	var mouse := InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_RIGHT
	InputMap.action_add_event(ACTION, mouse)
	eq(Settings.binding_text(ACTION), "RMB", "mouse binding labels remain available on touch devices")
	InputMap.erase_action(ACTION)
	eq(Settings.binding_text(ACTION), "", "removed or missing actions have no binding label")
	done()

func test_mobile_startup_aa_matches_compatibility_renderer() -> void:
	eq(ProjectSettings.get_setting("rendering/renderer/rendering_method.mobile"), "gl_compatibility", "mobile starts with the compatibility renderer")
	eq(ProjectSettings.get_setting("rendering/anti_aliasing/quality/screen_space_aa.mobile"), 0, "mobile startup does not request unsupported screen-space AA")
	eq(ProjectSettings.get_setting("rendering/anti_aliasing/quality/screen_space_aa"), 1, "desktop startup keeps its FXAA setting")
	done()
