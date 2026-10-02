extends SceneTree

func _initialize() -> void:
	assert(StatCalculator.HP_PER_STR == 6.0)
	assert(StatCalculator.HP_PER_WIS == 4.0)
	assert(StatCalculator.MANA_PER_INT == 4.0)
	assert(StatCalculator.MANA_PER_SPI == 3.0)
	assert(ClassDef.new().free_points_per_level == 10)
	assert(ClassDef.new().skill_points_per_level == 2)
	assert(DamagePipeline.EVADE_CAP == 0.65)
	assert(SkillDef.MOVEMENT_LIMITS[&"dash_strike"] == 8.0)
	var hashes := {}
	for path in ["core/stats/stat_calculator", "core/stats/combat_growth", "core/stats/enemy_stats", "core/progression/hero_progress", "core/defs/class_def", "core/defs/skill_def", "core/combat/damage_pipeline", "actors/actor", "actors/enemy/enemy", "actors/enemy/enemy_traits_x", "actors/player/player", "skills/skill_runner"]:
		var packed := "res://src/%s.gdc" % path
		assert(FileAccess.file_exists(packed))
		hashes["assets/src/%s.gdc" % path] = FileAccess.get_sha256(packed)
	var out := FileAccess.open("A:/Python/beyond-heroes/output/survival-packed-scripts.json", FileAccess.WRITE)
	out.store_string(JSON.stringify(hashes, "  "))
	out.close()
	print("PACKAGED BALANCE: verified pools, rewards, evasion, travel cap and 12 compiled scripts")
	quit(0)
