extends Node
## bh-031: bakes every townsperson's ID portrait (an ID shot of their model, PortraitStudio) to
## res://assets/ui/portraits/npc/<id>.png. Needs the real renderer (not --headless):
##   godot --path game res://tests/tools/bake_portraits.tscn [-- --only=maelis,hald] [-- --size=384]
## Re-run after changing a persona in DataPersonas.NPCS, then --import.

func _ready() -> void:
	Game.save_slot = 97
	_run.call_deferred()

func _arg(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name):
			return a.substr(name.length() + 3)
	return def

func _run() -> void:
	var only := _arg("only", "").split(",", false)
	var size := int(_arg("size", "384"))
	var dir := ProjectSettings.globalize_path(DataPersonas.PORTRAIT_DIR)
	DirAccess.make_dir_recursive_absolute(dir)
	var n := 0
	for id in DataPersonas.NPCS:
		if not only.is_empty() and not only.has(id):
			continue
		var img := await PortraitStudio.render_persona(DataPersonas.NPCS[id], size)
		if img == null:
			push_error("portrait failed: %s" % id)
			continue
		img.save_png(dir.path_join(id + ".png"))
		n += 1
		print("PORTRAIT ", id)
	print("BAKE_PORTRAITS_DONE ", n)
	get_tree().quit()
