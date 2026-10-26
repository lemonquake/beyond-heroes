extends SceneTree
## Run using WOA's project cache, with no import/mutation of source assets:
## godot --headless --path A:/Python/woa -s <absolute path to this file>
## Copies only Blood Ranger's four clips plus their exact source collision fixes.

const CLIPS := [&"bow_idle", &"bow_shoot", &"bow_hold", &"bow_loose"]

func _init() -> void:
	var destination := String(get_script().resource_path).get_base_dir().path_join("../../assets/characters/roles").simplify_path()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			destination = arg.substr(6).simplify_path()
	DirAccess.make_dir_recursive_absolute(destination)
	var src := load("res://assets/characters/hero/mocap/hero_mocap.res") as AnimationLibrary
	var arms := load("res://assets/characters/hero/mocap/collide/hero.res") as AnimationLibrary
	if src == null or arms == null:
		quit(1)
		return
	var library := AnimationLibrary.new()
	library.set_meta("hips_rest", src.get_meta("hips_rest"))
	library.set_meta("source", "Warriors of Aether Blood Ranger; mocap plus source collision repair")
	for name in CLIPS:
		var clip := src.get_animation(name).duplicate(true) as Animation
		if arms.has_animation(name):
			_copy_tracks(arms.get_animation(name), clip)
		library.add_animation(name, clip)
	var output := destination.path_join("blood_ranger_bow.res")
	var error := ResourceSaver.save(library, output, ResourceSaver.FLAG_COMPRESS)
	print("Blood Ranger source bow clips: ", library.get_animation_list(), " save=", error_string(error))
	if error == OK:
		var manifest := {"source_library_sha256": FileAccess.get_sha256("res://assets/characters/hero/mocap/hero_mocap.res"),
			"source_collision_sha256": FileAccess.get_sha256("res://assets/characters/hero/mocap/collide/hero.res"),
			"output_sha256": FileAccess.get_sha256(output), "clips": Array(CLIPS),
			"source_library": "WOA assets/characters/hero/mocap/hero_mocap.res",
			"source_collision": "WOA assets/characters/hero/mocap/collide/hero.res"}
		var file := FileAccess.open(destination.path_join("bow_manifest.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(manifest, "  ") + "\n")
	quit(0 if error == OK else 1)

func _copy_tracks(src: Animation, dst: Animation) -> void:
	for track in src.get_track_count():
		var bone := String(src.track_get_path(track)).get_slice(":", 1)
		for target in dst.get_track_count():
			if String(dst.track_get_path(target)).get_slice(":", 1) != bone or dst.track_get_type(target) != src.track_get_type(track):
				continue
			while dst.track_get_key_count(target) > 0:
				dst.track_remove_key(target, 0)
			for key in src.track_get_key_count(track):
				dst.track_insert_key(target, src.track_get_key_time(track, key), src.track_get_key_value(track, key))
