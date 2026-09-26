extends SceneTree
## Loads every GDScript in res://src and res://tests and reports the ones that fail to compile.
##   godot --headless --path game -s res://tests/tools/compile_all.gd

func _initialize() -> void:
	var bad := []
	var n := 0
	for dir in ["res://src", "res://tests"]:
		for p in _scripts(dir):
			n += 1
			var s: GDScript = load(p)
			if s == null or not s.can_instantiate() and not s.is_abstract():
				bad.append(p)
	print("COMPILE %d scripts, %d failed" % [n, bad.size()])
	for b in bad:
		print("  FAILED ", b)
	quit(1 if bad.size() > 0 else 0)

func _scripts(dir: String) -> Array:
	var out := []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".gd"):
			out.append(dir.path_join(f))
	for sub in d.get_directories():
		out.append_array(_scripts(dir.path_join(sub)))
	return out
