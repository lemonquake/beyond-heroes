extends Control
## Checks all fifteen boss-set descriptions against the visible screen at normal desktop scale.
var out := "res://../work/lemondev/tempo-armory/evidence/set-details"

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	get_window().size = Vector2i(1920, 1080)
	get_window().content_scale_size = Vector2i(1920, 1080)
	get_window().theme = UITheme.theme()
	out = ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(out)
	Game.save_slot = 96
	var rows := []
	var failures := []
	for entry in preload("res://src/data/data_boss_sets.gd").ROWS:
		var h := Game.new_hero(StringName(entry[2]), "Set details")
		h.progress.level = 60
		h.set_tier(DataGuilds.MAX_RANK)
		for slot in preload("res://src/data/data_boss_sets.gd").slots_for_set(StringName(entry[0])):
			h.equipment.slots[slot] = DB.make_item(preload("res://src/data/data_boss_sets.gd").piece_id(StringName(entry[0]), slot), BH.Rarity.MASTER, 60, 187)
		var item := h.equipment.get_item(&"armor")
		var card := Tips.item(item, {"hero": h, "compare": false})
		add_child(card)
		card.position = Vector2(80, 40)
		for i in 5:
			await get_tree().process_frame
		var bounds := card.get_global_rect()
		var fits := get_viewport_rect().encloses(bounds)
		rows.append({"set": entry[0], "width": bounds.size.x, "height": bounds.size.y, "fits": fits})
		if not fits:
			failures.append(entry[0])
		if entry[0] in ["dragonforge", "grievance_of_the_fairy", "wailing_mistress"] and DisplayServer.get_name() != "headless":
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(out.path_join(String(entry[0]) + ".png"))
		card.free()
	FileAccess.open(out.path_join("report.json"), FileAccess.WRITE).store_string(JSON.stringify({"sets": rows, "failures": failures}, "  "))
	print("SET_TOOLTIPS: ", rows.size(), " checked; failures ", failures)
	get_tree().quit(0 if failures.is_empty() else 1)
