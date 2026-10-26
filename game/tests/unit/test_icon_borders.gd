extends TestCase

class IsolatedSettings extends "res://src/autoload/settings.gd":
	func apply() -> void:
		pass
	func save_file() -> void:
		pass

func _init() -> void:
	strict = true

func test_styles_are_replaceable_and_missing_content_falls_back() -> void:
	var style := IconBorder.new()
	style.style_id = &"unit_border"
	style.display_name = "Unit Border"
	style.aperture = Rect2(0.1, 0.2, 0.7, 0.6)
	ok(IconBorders.register_style(style), "a cosmetic can add its own stable ID")
	eq(IconBorders.resolve(&"unit_border"), style, "registry resolves the new style")
	ok(not IconBorders.register_style(style), "accidental duplicate IDs are rejected")
	var replacement := style.duplicate() as IconBorder
	replacement.tint = Color.RED
	ok(IconBorders.register_style(replacement, true), "explicit replacement is supported")
	eq(IconBorders.resolve(&"unit_border").tint, Color.RED, "replacement supplies its tint")
	eq(IconBorders.resolve(&"unknown_cosmetic").style_id, IconBorders.DEFAULT_ID, "missing pack uses official frame")
	IconBorders.unregister_style(&"unit_border")
	eq(IconBorders.resolve(&"unit_border").style_id, IconBorders.DEFAULT_ID, "removed content falls back")
	IconBorders.unregister_style(IconBorders.DEFAULT_ID)
	eq(IconBorders.resolve(IconBorders.DEFAULT_ID).style_id, IconBorders.DEFAULT_ID, "official fallback cannot be removed")
	var customized := IconBorders.DEFAULT.duplicate() as IconBorder
	customized.tint = Color.CYAN
	ok(IconBorders.register_style(customized, true), "official style can be explicitly customized and replaced")
	eq(IconBorders.resolve(IconBorders.DEFAULT_ID).tint, Color.CYAN, "custom official style is used")
	IconBorders.unregister_style(IconBorders.DEFAULT_ID)
	eq(IconBorders.resolve(IconBorders.DEFAULT_ID), IconBorders.DEFAULT, "removing the official replacement restores its original")
	var saved := Settings.icon_border_style
	var missing := IconBorder.new()
	missing.style_id = &"missing_unit_border"
	missing.texture_path = "res://assets/ui/borders/absent_unit_test.png"
	missing.aperture = Rect2(0.2, 0.2, 0.6, 0.6)
	ok(IconBorders.register_style(missing), "a pack's metadata can be registered before its texture")
	Settings.icon_border_style = "missing_unit_border"
	eq(IconBorders.current(), IconBorders.DEFAULT, "missing texture falls back with matching aperture and tint")
	eq(Settings.icon_border_style, "missing_unit_border", "fallback does not erase a saved cosmetic preference")
	Settings.icon_border_style = saved
	IconBorders.unregister_style(&"missing_unit_border")
	done()

func test_aperture_scales_in_both_axes_and_invalid_geometry_is_rejected() -> void:
	var style := IconBorder.new()
	style.style_id = &"invalid_unit_border"
	style.aperture = Rect2(0.1, 0.2, 0.7, 0.6)
	var inner := style.content_rect(Rect2(20, 40, 100, 200))
	near(inner.position.x, 30, 0.001, "horizontal inset")
	near(inner.position.y, 80, 0.001, "vertical inset")
	near(inner.size.x, 70, 0.001, "opening width")
	near(inner.size.y, 120, 0.001, "opening height")
	style.aperture = Rect2(0.1, 0.1, 1.0, 1.0)
	ok(not IconBorders.register_style(style), "out of bounds artwork cannot be registered")
	style.aperture = Rect2(0.2, 0.2, -0.1, 0.5)
	ok(not style.is_valid(), "negative apertures are invalid")
	done()

func test_border_preference_is_a_device_setting_and_loads_legacy_files() -> void:
	const FIXTURE := "user://icon-border-test.cfg"
	var settings := IsolatedSettings.new()
	eq(settings.to_dict().icon_border_style, "aether_forged", "default participates in serialization")
	settings.icon_border_style = "future_paid_border"
	settings.from_dict({"icon_border_style": "another_hero_border"})
	eq(settings.icon_border_style, "future_paid_border", "loading another hero keeps this device's style")
	var config := ConfigFile.new()
	config.set_value("settings", "icon_border_style", "future_paid_border")
	eq(config.save(FIXTURE), OK, "isolated preference fixture writes")
	settings.load_file(FIXTURE)
	eq(settings.icon_border_style, "future_paid_border", "stable IDs survive settings file loading")
	settings.free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(FIXTURE))
	done()
