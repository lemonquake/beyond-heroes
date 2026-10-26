extends SceneTree
## External pack-only validation. Does not reference project classes or raw source PNG bytes.
## godot --headless --main-pack <BeyondHeroes.exe> --script <absolute path to this file>
## Optional user flags: --probe-out=<absolute.json> --expect-count=519 --expect-routes=495

var failures: Array[String] = []
var checks := 0
var official_loaded := 0
var retained_loaded := 0
var border_max_alpha := -1.0
var output := ""
var expected_count := 519
var expected_routes := 495

func _initialize() -> void:
	output = get_script().resource_path.get_base_dir().path_join("pack-probe.json")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--probe-out="):
			output = arg.substr(12)
		elif arg.begins_with("--expect-count="):
			expected_count = int(arg.substr(15))
		elif arg.begins_with("--expect-routes="):
			expected_routes = int(arg.substr(16))
	_run.call_deferred()

func _check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)

func _texture(path: String, official: bool) -> void:
	var exists := ResourceLoader.exists(path)
	_check(exists, "Missing imported texture: " + path)
	if not exists:
		return
	var resource := ResourceLoader.load(path)
	_check(resource is Texture2D, "Resource is not a Texture2D: " + path)
	if not resource is Texture2D:
		return
	var texture: Texture2D = resource
	if official:
		_check(texture.get_size() == Vector2(256, 256), "Incorrect official icon dimensions: " + path)
		official_loaded += 1
	else:
		_check(texture.get_width() > 0 and texture.get_height() > 0, "Empty retained item texture: " + path)
		retained_loaded += 1

func _run() -> void:
	var path := "res://assets/ui/official/manifest.json"
	_check(FileAccess.file_exists(path), "Official manifest is absent from the exported pack")
	var manifest: Dictionary = {}
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		_check(parsed is Dictionary, "Official manifest cannot be parsed")
		if parsed is Dictionary:
			manifest = parsed
	var artifacts: Dictionary = manifest.get("artifacts", {})
	var routes: Dictionary = manifest.get("routes", {})
	var retained: Dictionary = manifest.get("retained_artifacts", {})
	_check(int(manifest.get("count", -1)) == expected_count, "Manifest artwork count differs from the expected revision")
	_check(artifacts.size() == expected_count, "Artifact registry count differs from the expected revision")
	_check(routes.size() == expected_routes, "Route registry count differs from the expected revision")
	_check(not retained.is_empty(), "Retained item artwork registry is empty")
	var artifact_paths := {}
	for key in artifacts:
		var target := String(artifacts[key].get("path", ""))
		_check(target.begins_with("res://assets/ui/official/") and target.ends_with(".png"), "Artifact route is not a painted PNG: " + String(key))
		_check(not artifact_paths.has(target), "Duplicate official artifact path: " + target)
		artifact_paths[target] = true
		_texture(target, true)
	for source in routes:
		var target := String(routes[source])
		_check(artifact_paths.has(target), "Legacy route resolves outside the artwork registry: " + String(source))
		_check(ResourceLoader.exists(target), "Legacy route resolves to an absent imported texture: " + String(source))
	for family in ["skills", "tempo_skills", "signatures", "upgrades"]:
		var identities: Dictionary = manifest.get(family, {})
		_check(not identities.is_empty(), "Missing identity family: " + family)
		for id in identities:
			_check(artifact_paths.has(String(identities[id])), "Missing identity artwork: %s/%s" % [family, id])
	for retained_path in retained:
		_texture(String(retained_path), false)
	_probe_border()
	var summary := {"engine": Engine.get_version_info().string, "checks": checks, "failures": failures,
		"manifest_count": manifest.get("count", 0), "artifact_count": artifacts.size(), "route_count": routes.size(),
		"official_textures_loaded": official_loaded, "retained_textures_loaded": retained_loaded,
		"border_center_max_alpha": border_max_alpha, "passed": failures.is_empty()}
	DirAccess.make_dir_recursive_absolute(output.get_base_dir())
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(summary, "  ") + "\n")
		file.close()
	else:
		failures.append("Could not write probe summary: " + output)
	print("OFFICIAL_PACK_PROBE ", JSON.stringify(summary))
	quit(0 if failures.is_empty() else 1)

func _probe_border() -> void:
	var path := "res://assets/ui/borders/aether_forged.png"
	_check(ResourceLoader.exists(path), "Default border is absent from the exported pack")
	if not ResourceLoader.exists(path):
		return
	var texture: Texture2D = ResourceLoader.load(path)
	_check(texture != null, "Default border cannot be loaded as an imported texture")
	if texture == null:
		return
	var image := texture.get_image()
	_check(image != null, "Imported border pixels are unavailable")
	if image == null:
		return
	if image.is_compressed():
		_check(image.decompress() == OK, "Imported border could not be decompressed")
	var start := Vector2i(image.get_size() * 0.25)
	var end := Vector2i(image.get_size() * 0.75)
	border_max_alpha = 0.0
	for y in range(start.y, end.y):
		for x in range(start.x, end.x):
			border_max_alpha = maxf(border_max_alpha, image.get_pixel(x, y).a)
	_check(border_max_alpha <= 1.0 / 255.0 + 0.00001, "Imported border opening contains an opaque matte or checkerboard")
