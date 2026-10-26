class_name IconBorders
extends RefCounted
## Stable cosmetic IDs, independent of item/skill IDs and rarity. Content ownership is checked by the caller.

const DEFAULT_ID := &"aether_forged"
const DEFAULT := preload("res://assets/ui/borders/aether_forged.tres")
static var _styles: Dictionary = {}

static func _ensure() -> void:
	if not _styles.has(DEFAULT_ID):
		_styles[DEFAULT_ID] = DEFAULT

## Register only styles the player may use. Replacing an existing ID requires explicit replacement.
static func register_style(style: IconBorder, replace := false) -> bool:
	_ensure()
	if style == null or not style.is_valid() or (_styles.has(style.style_id) and not replace):
		return false
	_styles[style.style_id] = style
	Settings.changed.emit()
	return true

static func unregister_style(style_id: StringName) -> void:
	_ensure()
	if style_id == DEFAULT_ID:
		_styles[DEFAULT_ID] = DEFAULT
		Settings.changed.emit()
	elif _styles.erase(style_id):
		Settings.changed.emit()

static func styles() -> Array:
	_ensure()
	return _styles.values()

static func resolve(style_id: StringName) -> IconBorder:
	_ensure()
	return _styles.get(style_id, DEFAULT)

static func current() -> IconBorder:
	var selected := resolve(StringName(Settings.icon_border_style))
	return selected if selected.texture() != null else DEFAULT

static func content_rect(bounds: Rect2) -> Rect2:
	return current().content_rect(bounds)

static func draw_frame(canvas: CanvasItem, bounds: Rect2, modulate := Color.WHITE) -> void:
	var style := current()
	var frame := style.texture()
	if frame == null and style.style_id != DEFAULT_ID:
		frame = DEFAULT.texture()
	if frame:
		canvas.draw_texture_rect(frame, bounds, false, style.tint * modulate)
	else:
		# Remains usable when a cosmetic texture is unavailable or a content pack was removed.
		canvas.draw_rect(bounds.grow(-bounds.size.x * 0.025), Color(0.6, 0.5, 0.34, modulate.a), false, maxf(1.0, bounds.size.x * 0.025))
