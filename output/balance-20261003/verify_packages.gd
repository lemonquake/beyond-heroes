extends SceneTree

func _initialize() -> void:
	var root := "A:/Python/beyond-heroes/"
	var apk := ZIPReader.new()
	if apk.open(root + "build/BeyondHeroes.apk") != OK or not ProjectSettings.load_resource_pack(root + "build/windows/BeyondHeroes.exe", true):
		push_error("Cannot open packaged game resources")
		quit(1)
		return
	var checks := {}
	var passed := true
	for path in ["src/actors/actor.gdc", "src/core/combat/status_controller.gdc", "src/core/combat/damage_pipeline.gdc", "src/core/progression/tree_def.gdc", "src/core/progression/tree_state.gdc", "src/core/defs/skill_def.gdc", "src/data/data_crystals.gdc", "src/core/crafting/crafting.gdc", "src/loot/loot_pools.gdc"]:
		var windows := FileAccess.get_file_as_bytes("res://" + path)
		var android := apk.read_file("assets/" + path)
		var same := not windows.is_empty() and windows == android
		checks[path] = {"bytes": windows.size(), "identical": same}
		passed = passed and same
		print(path, ": identical Windows/Android compiled script = ", same)
	apk.close()
	var report := FileAccess.open(root + "output/balance-20261003/package-source-check.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"passed": passed, "scripts": checks}, "  "))
	quit(0 if passed else 1)
