class_name OfficialIcons
extends RefCounted
## Artwork redirects keep authored images independent from gameplay definitions and cosmetic borders.

const MANIFEST := "res://assets/ui/official/manifest.json"
static var _data: Dictionary = {}
static var _loaded := false

static func manifest() -> Dictionary:
	if not _loaded:
		_loaded = true
		if FileAccess.file_exists(MANIFEST):
			var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
			if parsed is Dictionary:
				_data = parsed
	return _data

static func path(source: String) -> String:
	var replacement := String(manifest().get("routes", {}).get(source, ""))
	return replacement if replacement != "" and ResourceLoader.exists(replacement) else source

static func identity(family: String, id: String) -> String:
	var replacement := String(manifest().get(family, {}).get(id, ""))
	return replacement if replacement != "" and ResourceLoader.exists(replacement) else ""
