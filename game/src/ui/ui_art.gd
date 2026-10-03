class_name UIArt
## Access to the painted UI art (game/assets/ui) described by ui_art_manifest.json: 9-slice styles at the intended
## scale, plain textures, per-texture metadata (bar windows, orb centres, icon rects), and icon lookups.

const ROOT := "res://assets/ui/"
const MANIFEST := "res://assets/ui/ui_art_manifest.json"
const SCALE := 0.5

static var _manifest := {}
static var _tex := {}
static var _styles := {}

static func manifest() -> Dictionary:
	if _manifest.is_empty() and FileAccess.file_exists(MANIFEST):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest

static func meta(path: String) -> Dictionary:
	return manifest().get(path, {})

static func tex(path: String) -> Texture2D:
	if not _tex.has(path):
		var p := path if path.begins_with("res://") else ROOT + path
		_tex[path] = load(p) if ResourceLoader.exists(p) else null
	return _tex[path]

## Logical size (at 1920x1080) of a texture: texture size x its draw scale.
static func size_of(path: String) -> Vector2:
	var t := tex(path)
	if t == null:
		return Vector2.ZERO
	return t.get_size() * float(meta(path).get("scale", SCALE) if meta(path).get("scale") != null else SCALE)

## A 9-slice style for a manifest texture. `content` overrides the content margins (logical px, l/t/r/b).
static func style(path: String, content := [], mod := Color.WHITE, center := true) -> ArtStyleBox:
	var key := "%s|%s|%s|%s" % [path, content, mod, center]
	if _styles.has(key):
		return _styles[key]
	var m := meta(path)
	var sb := ArtStyleBox.new()
	sb.texture = tex(path)
	var s := float(m.get("scale", SCALE)) if m.get("scale") != null else SCALE
	sb.draw_scale = s
	var mg: Array = m.get("margins", [0, 0, 0, 0]) if m.get("margins") != null else [0, 0, 0, 0]
	sb.margins = PackedInt32Array(mg)
	var ex: Array = m.get("expand_margins", [0, 0, 0, 0])
	sb.expand = PackedInt32Array(ex)
	sb.modulate = mod
	sb.draw_center = center
	var cm: Array = content if not content.is_empty() else (m.get("content_margins", mg) as Array).map(func(v): return float(v) * s)
	sb.content_margin_left = cm[0]
	sb.content_margin_top = cm[1]
	sb.content_margin_right = cm[2]
	sb.content_margin_bottom = cm[3]
	_styles[key] = sb
	return sb

## TextureRect showing a texture at its logical size (keeps aspect, stays crisp at 4K).
static func image(path: String, size := Vector2.ZERO) -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex(path)
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.custom_minimum_size = size if size != Vector2.ZERO else size_of(path)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r

# ---- Icons ---------------------------------------------------------------------------------------------------------

static func icon(category: String, id: String) -> Texture2D:
	for ext in [".svg", ".png"]:
		var p := ROOT + "icons/%s/%s%s" % [category, id, ext]
		if ResourceLoader.exists(p):
			return tex(p)
	return null

static func ui_icon(id: String) -> Texture2D:
	return icon("ui", id)

static func status_icon(status_id: StringName) -> Texture2D:
	var path := StatusRules.icon_of(status_id)
	if path != "" and ResourceLoader.exists(path):
		return tex(path)
	return icon("status", String(status_id))

static func element_icon(e: int) -> Texture2D:
	return icon("elements", String(Elements.NAMES[e]).to_lower())

static func attribute_icon(attr: StringName) -> Texture2D:
	return icon("attributes", BH.ATTRIBUTE_ICONS.get(attr, String(attr)))

static func skill_icon(skill_id: StringName) -> Texture2D:
	var s := DB.skill(skill_id)
	if s != null and s.icon != "" and ResourceLoader.exists(s.icon):
		return tex(s.icon)
	return icon("skills", String(skill_id))

## Icon of a tree node ({"icon": res path}) with the skill icon as fallback.
static func node_icon(n: Dictionary) -> Texture2D:
	var p := String(n.get("icon", ""))
	if p != "" and ResourceLoader.exists(p):
		return tex(p)
	if n.has("skill"):
		return skill_icon(n.skill)
	return null

static func rarity_frame(r: int) -> Texture2D:
	return tex("slots/rarity_%d.png" % clampi(r, 0, BH.RARITY_COUNT - 1))

static func rarity_glow(r: int) -> Texture2D:
	return tex("slots/rarity_glow_%d.png" % r) if r >= 5 else null

static func portrait(id: String) -> Texture2D:
	return tex("portraits/%s.svg" % id)
