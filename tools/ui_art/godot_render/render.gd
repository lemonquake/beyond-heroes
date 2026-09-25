extends SceneTree
# Usage: godot --headless --path tools/ui_art/godot_render --script render.gd -- <list_file>
# list_file lines: <svg_path>|<scale>|<png_out>
func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 1:
		push_error("need list file")
		quit(2)
		return
	var f := FileAccess.open(args[0], FileAccess.READ)
	var ok := 0
	var bad := 0
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line == "":
			continue
		var parts := line.split("|")
		var src := FileAccess.get_file_as_string(parts[0])
		var img := Image.new()
		var err := img.load_svg_from_string(src, float(parts[1]))
		if err != OK or img.is_empty():
			print("FAIL ", parts[0], " err=", err)
			bad += 1
			continue
		img.save_png(parts[2])
		ok += 1
	print("RENDERED ok=", ok, " fail=", bad)
	quit(0 if bad == 0 else 1)
