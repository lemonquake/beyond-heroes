extends TestCase

func _init() -> void:
	strict = true

func test_remote_set_appearance_updates_reuses_and_clears() -> void:
	var avatar := NetAvatar.new().setup(17, "p", {"name": "Set wearer", "lvl": 30})
	host.add_child(avatar)
	var app := {"model": DB.class_def(&"knight").model_path, "scale": 1.0, "pers": "knight",
		"weapons": {}, "set_gear": {"helm": "boss_dragonforge_helm", "armor": "boss_dragonforge_armor"}}
	avatar.set_appearance(app)
	eq(_main(avatar), 2, "remote crown and armor attached")
	var first := avatar.visual._set_nodes[0]
	avatar.set_appearance(app.duplicate(true))
	eq(avatar.visual._set_nodes[0], first, "identical network update reuses geometry")
	eq(avatar.visual.appearance.set_gear.size(), 2, "appearance retains both pieces")
	app.set_gear = {"helm": "boss_dragonforge_armor", "armor": "unknown_item"}
	avatar.set_appearance(app)
	eq(_main(avatar), 0, "invalid slot and unknown item ignored")
	app.set_gear = {"helm": "boss_truth_of_raikuru_helm"}
	avatar.set_appearance(app)
	eq(_main(avatar), 1, "new set attachment replaces previous gear")
	app.erase("set_gear")
	avatar.set_appearance(app)
	eq(_main(avatar), 0, "older peer payload clears cosmetic equipment")
	avatar.queue_free()
	await host.get_tree().process_frame
	done()

## Worn pieces ("Set_<slot>"), not their per-bone parts (bh-022 pauldrons, hand plates, sabatons, tassets).
func _main(avatar: NetAvatar) -> int:
	return avatar.visual._set_nodes.filter(func(n): return String(n.name).begins_with("Set_")).size()
