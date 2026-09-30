class_name EnemyStats
## Derived stats of an enemy: EnemyDef level-1 values scaled by level and difficulty, plus elite and runtime
## modifiers (statuses). Uses the same modifier algebra as StatCalculator (flat, then increased, then more) so buffs,
## debuffs and elite affixes behave identically on heroes and monsters.

const RES_CAP := 0.9
const LEVEL_DEFENSE := 0.10      # +10% defense per level above 1
const LEVEL_ACCURACY := 4.0
const LEVEL_EVASION := 2.0

static func build(def: EnemyDef, level: int, difficulty: Dictionary, modifiers: Array, elite := false, boss := false) -> DerivedStats:
	var d := DerivedStats.new()
	d.level = level
	d.set_stat(&"difficulty_hp", maxf(0.1, float(difficulty.get("hp", 1.0))))
	d.loadout = WeaponLoadout.new()
	d.affinity = def.affinity
	var agg := StatCalculator.Aggregate.new()
	for m in modifiers:
		var sm := m as StatModifier
		if sm == null:
			continue
		if String(sm.stat).begins_with("flag_"):
			var fk := StringName(String(sm.stat).substr(5))
			d.flags[fk] = d.flags.get(fk, 0.0) + sm.value
			continue
		agg.add(sm)
	var scale := def.scaled(level)
	var hp_mult := float(difficulty.get("hp", 1.0)) * (2.6 if elite else 1.0)
	var dmg_mult := float(difficulty.get("damage", 1.0)) * (1.3 if elite else 1.0)
	_set_stat(d, agg, &"max_hp", def.hp * scale * hp_mult * CombatGrowth.health_factor(level) * CombatGrowth.enemy_health_bonus(level), 1.0)
	_set_stat(d, agg, &"max_mana", 30.0 + level * 3.0, 0.0)
	_set_stat(d, agg, &"defense", def.defense * (1.0 + LEVEL_DEFENSE * float(level - 1)), 0.0)
	_set_stat(d, agg, &"evasion", def.evasion + LEVEL_EVASION * float(level - 1), 0.0)
	_set_stat(d, agg, &"accuracy", def.accuracy + LEVEL_ACCURACY * float(level - 1), 1.0)
	_set_stat(d, agg, &"crit_chance", def.crit_chance, 0.0, StatCalculator.CRIT_CAP)
	var cd := maxf(1.0, StatCalculator.CRIT_DAMAGE_BASE + agg.flat(&"crit_damage")) * agg.more(&"crit_damage")
	d.set_stat(&"crit_damage", cd)
	_set_stat(d, agg, &"move_speed", def.move_speed, def.move_speed * 0.15, def.move_speed * 1.8)
	var as_raw := agg.inc(&"attack_speed") + agg.flat(&"attack_speed")
	d.set_stat(&"attack_speed", clampf((1.0 + StatCalculator.soften(as_raw)) * agg.more(&"attack_speed"), StatCalculator.SPEED_MULT_MIN, StatCalculator.SPEED_MULT_MAX))
	d.set_stat(&"cast_speed", d.get_stat(&"attack_speed"))
	_set_stat(d, agg, &"knockback_res", def.knockback_res, 0.0, 0.95)
	_set_stat(d, agg, &"status_res", def.status_res + float(difficulty.get("status_res", 0.0)), 0.0, 0.9)
	_set_stat(d, agg, &"poise", def.poise * def.stagger_resist * (1.0 + 0.05 * float(level - 1)) * (1.8 if elite else 1.0), 1.0)
	_set_stat(d, agg, &"impact_strength", 1.0, 0.1)
	_set_stat(d, agg, &"block_chance", 0.0, 0.0, 0.9)
	_set_stat(d, agg, &"block_strength", 0.7 if def.blocks_front else 0.4, 0.0, 1.0)
	if boss:
		d.set_stat(&"boss_damage_taken", CombatGrowth.BOSS_DAMAGE_TAKEN)
		d.set_stat(&"boss_hit_limit", minf(d.get_stat(&"max_hp") * CombatGrowth.BOSS_HIT_SHARE, CombatGrowth.boss_hit_ceiling(level)))
	d.set_stat(&"damage_mult", dmg_mult * scale * CombatGrowth.enemy_damage_bonus(level))
	d.set_stat(&"phys_res_flat", agg.flat(&"phys_res"))
	var od := agg.more(&"outgoing_damage") * (1.0 + agg.inc(&"outgoing_damage"))
	d.set_stat(&"outgoing_damage", maxf(0.05, od))
	var dt := agg.more(&"damage_taken") * (1.0 + agg.inc(&"damage_taken"))
	d.set_stat(&"damage_taken", maxf(0.05, dt))
	for k in [&"life_leech", &"elemental_damage", &"status_power", &"stagger_power", &"pen_armor", &"damage"]:
		d.set_stat(k, agg.flat(k) + agg.inc(k))
	for e in Elements.ELEMENTAL:
		var rk := Elements.res_key(e)
		var base := float(def.resistances.get(e, 0.0))
		d.set_stat(rk, clampf(base + agg.flat(rk) + agg.flat(&"res_all"), StatCalculator.RES_FLOOR, RES_CAP))
		d.set_stat(Elements.dmg_key(e), agg.flat(Elements.dmg_key(e)) + agg.inc(Elements.dmg_key(e)))
		d.set_stat(Elements.pen_key(e), agg.flat(Elements.pen_key(e)))
	for e in def.immune:
		d.immune[int(e)] = true
	return d

static func _set_stat(d: DerivedStats, agg: StatCalculator.Aggregate, k: StringName, base: float, lo := -INF, hi := INF) -> void:
	var v := (base + agg.flat(k)) * (1.0 + agg.inc(k)) * agg.more(k)
	d.set_stat(k, clampf(v, lo, hi))

## Damage range of an enemy attack after level/difficulty scaling (before the pipeline's bonuses).
static func attack_range(def: EnemyDef, stats: DerivedStats, mult: float) -> Vector2:
	var m := stats.get_stat(&"damage_mult", 1.0) * mult
	return Vector2(def.damage_min * m, def.damage_max * m)

## A persistent build snapshot gives roughly 25-45 seconds of basic attacking
## before defenses, movement and skill use. No in-combat rubber-banding.
static func boss_health(hero: HeroData, baseline: DerivedStats) -> float:
	var stats := hero.compute_stats()
	ItemCompare._add_weapon_rows(stats)
	var dps := stats.get_stat(&"weapon_dps")
	var burst := ItemCompare.basic_hit(stats) * stats.get_stat(&"crit_damage", 1.5)
	for id in hero.learned_skills():
		var skill := DB.skill(id)
		var params := hero.resolved_skill(id)
		if skill == null or not params.has("damage_min") or skill.kind != DamageRequest.Kind.SPELL:
			continue
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = stats
		req.target = DerivedStats.new()
		req.base_min = float(params.damage_min)
		req.base_max = float(params.get("damage_max", req.base_min))
		req.conversion = {skill.element: 1.0}
		var hit := float(DamagePipeline.preview(req).total)
		var interval := maxf(1.0 / stats.get_stat(&"cast_speed", 1.0), skill.cooldown * (1.0 - stats.get_stat(&"cdr")))
		dps = maxf(dps, hit / interval)
		burst = maxf(burst, hit * stats.get_stat(&"crit_damage", 1.5))
	var difficulty_hp := baseline.get_stat(&"difficulty_hp", 1.0)
	dps *= CombatGrowth.BOSS_DAMAGE_TAKEN * difficulty_hp
	burst *= CombatGrowth.BOSS_DAMAGE_TAKEN
	var reference_dps := CombatGrowth.BOSS_DAMAGE_TAKEN * difficulty_hp * (9.0 + 1.9 * baseline.level) * CombatGrowth.weapon_factor(baseline.level) * (1.0 + CombatGrowth.damage_increase(baseline.level * 0.04)) * 1.5
	return maxf(reference_dps * 20.0, maxf(burst * 4.0, clampf(baseline.get_stat(&"max_hp"), dps * 25.0, dps * 45.0)))
