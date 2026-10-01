extends Node
## bh-028 evasion investigation: what Evasion really does for agile heroes as they level.
##   godot --headless --path game res://tests/tools/probe_evasion.tscn
## Builds Ranger and Shadowblade heroes at each level the way the game spends points (class majors 3:2:1), with the
## class's evasion passives at full rank, then reports the evade chance against the real monster roster and the share
## of monster attacks that Evasion can apply to at all.

const LEVELS := [10, 20, 30, 40, 50, 60, 80, 100, 120]

func _ready() -> void:
	var out := PackedStringArray()
	# Which monster attacks can be evaded at all (DamagePipeline only rolls Evasion for req.evadable).
	var evadable_kinds := ["melee", "dash", "charge", "projectile", "chain", "tongue"]
	var by_band := {}
	for e: EnemyDef in DB.enemies.values():
		if e.attacks.is_empty() or e.damage_max <= 0.0:
			continue
		var band := "boss" if e.archetype == &"boss" else "monster"
		var b: Dictionary = by_band.get_or_add(band, {"w": 0.0, "ev": 0.0, "acc": []})
		b.acc.append(e.accuracy)
		for a in e.attacks:
			var w := float(a.get("weight", 1.0)) * (1.5 if a.kind in ["aoe", "charge", "pools", "summon"] else 1.0)
			if a.kind in ["summon"]:
				continue
			b.w += w
			if a.kind in evadable_kinds:
				b.ev += w
	for band in by_band:
		var b: Dictionary = by_band[band]
		var accs: Array = b.acc
		accs.sort()
		out.append("%s attacks Evasion can apply to: %.0f%% (weighted by how often they are chosen); base Accuracy %d-%d (median %d)" % [
			band, 100.0 * b.ev / maxf(1.0, b.w), accs[0], accs[-1], accs[accs.size() / 2]])
	out.append("")
	out.append("dungeon (first floor level) | evadable share of pack attacks | of the boss's attacks")
	for id in DataDungeons.order():
		var d := DataDungeons.get_def(id)
		var ids: Array = []
		for k in ["a", "b", "seal"]:
			ids.append_array(d.pools.get(k, []))
		out.append("%s (%d) | %.0f%% | %.0f%%" % [id, int(d.levels[0][0]), 100.0 * _share(ids, evadable_kinds), 100.0 * _share([d.boss], evadable_kinds)])
	out.append("")
	out.append("class | lvl | AGI | Evasion | vs median foe | vs most accurate foe | vs boss (+lvl2) | sheet says")
	for cid in [&"ranger", &"shadowblade"]:
		for lv in LEVELS:
			var h := Game.new_hero(cid, "Probe")
			h.progress.add_xp(XpCurve.total_xp_for_level(lv))
			h.progress.allocate_along_build(h.progress.free_points)
			var mods: Array = h.cls.class_modifiers.duplicate()
			# full-rank evasion passives (Light Feet / Evasion skill + Elusive / Blur talents)
			mods.append(StatModifier.inc(&"evasion", 0.12 + 0.05 * 24, "skill passive r25"))
			mods.append(StatModifier.inc(&"evasion", 0.24, "talent 3/3"))
			var cls := h.cls.duplicate() as ClassDef
			cls.class_modifiers = []
			var st := StatCalculator.compute(cls, lv, h.progress.base_attributes(), mods, WeaponLoadout.new())
			var eva := st.get_stat(&"evasion")
			var med := DataEnemies.build().filter(func(e): return e.accuracy > 0.0).map(func(e): return e.accuracy)
			med.sort()
			var med_acc: float = med[med.size() / 2] + EnemyStats.LEVEL_ACCURACY * (lv - 1)
			var max_acc: float = med[-1] + EnemyStats.LEVEL_ACCURACY * (lv - 1)
			var boss_acc: float = 64.0 + EnemyStats.LEVEL_ACCURACY * (lv + 1)
			out.append("%s | %d | %d | %d | %.0f%% | %.0f%% | %.0f%% | %.0f%%" % [cid, lv, st.get_stat(&"agi"), eva,
				100 * DamagePipeline.evade_chance(eva, med_acc), 100 * DamagePipeline.evade_chance(eva, max_acc),
				100 * DamagePipeline.evade_chance(eva, boss_acc), 100 * st.get_stat(&"evade_chance")])
	var text := "\n".join(out)
	print(text)
	var dir := ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-028/evidence")
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(dir.path_join("evasion_probe.txt"), FileAccess.WRITE)
	if f:
		f.store_string(text + "\n")
	get_tree().quit()

func _share(ids: Array, kinds: Array) -> float:
	var w := 0.0
	var ev := 0.0
	for id in ids:
		var e := DB.enemy(StringName(id))
		if e == null:
			continue
		for a in e.attacks:
			if a.kind == "summon":
				continue
			var x := float(a.get("weight", 1.0)) * (1.5 if a.kind in ["aoe", "charge", "pools"] else 1.0)
			w += x
			if a.kind in kinds:
				ev += x
	return ev / maxf(w, 0.001)
