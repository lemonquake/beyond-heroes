class_name StatCalculator
## THE centralized stat calculation system. Every derived statistic of a hero is computed here and nowhere else.
## Each result carries explanation lines so the character screen can show how it was calculated.

# ---- Tunable coefficients (single source of truth) -------------------------------------------------------
const HP_PER_STR := 2.0
const HP_PER_SPI := 1.0
const MANA_PER_INT := 2.0
const MANA_PER_WIS := 1.0
const MANA_PER_SPI := 0.5
const HP_REGEN_BASE := 0.2
const HP_REGEN_PER_SPI := 0.06
const HP_REGEN_PER_LEVEL := 0.04
const MANA_REGEN_BASE := 0.8
const MANA_REGEN_PER_WIS := 0.10
const MANA_REGEN_PER_SPI := 0.04
const MANA_REGEN_PER_INT := 0.02
const DEFENSE_PER_STR := 0.5
const ARMOR_K_BASE := 40.0          # phys DR = def / (def + ARMOR_K_BASE + ARMOR_K_LEVEL * attacker_level)
const ARMOR_K_LEVEL := 12.0
const RES_CAP := 0.75
const RES_FLOOR := -1.0
const RES_PER_WIS := 0.0015
const EVASION_PER_AGI := 2.0
const ACCURACY_PER_DEX := 3.0
const ACCURACY_PER_LEVEL := 2.0
const CRIT_PER_DEX := 0.0008
const CRIT_CAP := 0.80
const CRIT_DAMAGE_BASE := 1.5
const MOVE_PER_AGI := 0.0025
const MOVE_PER_STR := 0.002         # Strength carries the load: +0.2% movement speed per point
const CARRY_BASE := 55.0
const CARRY_PER_STR := 1.6
const LOAD_FREE := 0.35             # no slowdown up to 35% load
const LOAD_SLOW_MAX := 0.30         # ... then up to 30% less movement speed at 100% load
const OVERBURDEN_SLOW := 0.45       # 100%+ load: 45% less movement speed and no dodging
const MOVE_MAX_FACTOR := 1.5        # hard cap: 150% of the class base speed
const MOVE_MIN_FACTOR := 0.35
const ATK_SPEED_PER_AGI := 0.003
const CAST_SPEED_PER_AGI := 0.001
const CAST_SPEED_PER_WIS := 0.0015
const SPEED_SOFTCAP := 1.5          # diminishing returns: eff = raw / (1 + raw / SOFTCAP)
const SPEED_MULT_MIN := 0.4
const SPEED_MULT_MAX := 2.2         # animation-rate hard cap
const BLOCK_PER_DEX := 0.001
const BLOCK_CAP := 0.75
const GUARD_BLOCK_STRENGTH := 0.4   # block strength when guarding without a shield
const BLOCK_STR_PER_STR := 0.002
const CDR_PER_WIS := 0.001
const CDR_CAP := 0.40
const MCR_PER_WIS := 0.0012
const MCR_CAP := 0.30
const STATUS_RES_PER_SPI := 0.003
const STATUS_RES_CAP := 0.75
const KB_RES_PER_STR := 0.002
const KB_RES_CAP := 0.80
const IMPACT_PER_STR := 0.005
const MAGIC_PER_INT := 0.01
const MAGIC_PER_WIS := 0.003
const ELEM_PER_INT := 0.002
const HEAL_PER_SPI := 0.005
const BUFF_PER_SPI := 0.003
const PROJ_SPEED_PER_DEX := 0.002
const DODGE_CDR_PER_AGI := 0.002
const DODGE_CDR_CAP := 0.4
const POISE_PER_STR := 0.5
const STAGGER_PER_STR := 0.004       # +0.4% stagger strength per Strength
const CRIT_PER_AGI := 0.0004         # Agility's critical bonus: +0.04% critical chance per point (Dexterity is the main source)
const DODGE_DIST_PER_AGI := 0.0015
const DODGE_DIST_CAP := 0.30
const BUFF_PER_WIS := 0.004
const LIGHTDARK_PER_SPI := 0.0025    # Spirit attunes to Light and Dark: +0.25% damage, +0.1% resistance per point
const LIGHTDARK_RES_PER_SPI := 0.001
const PROJ_DMG_PER_DEX := 0.003
const PARRY_BASE := 0.18
const PARRY_PER_DEX := 0.0008
const PARRY_MAX := 0.32
const DEFAULT_ENEMY_EVASION_PER_LEVEL := 6.0   # reference target for the hit-chance display
const UNARMED_MIN := 2.0
const UNARMED_MAX := 4.0

## Modifier buckets for one stat.
class Bucket:
	var flat := 0.0
	var inc := 0.0
	var more := 1.0
	var lines := PackedStringArray()

class Aggregate:
	var buckets := {}
	func add(m: StatModifier) -> void:
		var b: Bucket = buckets.get(m.stat)
		if b == null:
			b = Bucket.new()
			buckets[m.stat] = b
		match m.op:
			StatModifier.Op.FLAT: b.flat += m.value
			StatModifier.Op.INC: b.inc += m.value
			StatModifier.Op.MORE: b.more *= (1.0 + m.value)
		if m.source != "":
			b.lines.append("%s  (%s)" % [m.describe(), m.source])
	func flat(s: StringName) -> float:
		return buckets[s].flat if buckets.has(s) else 0.0
	func inc(s: StringName) -> float:
		return buckets[s].inc if buckets.has(s) else 0.0
	func more(s: StringName) -> float:
		return buckets[s].more if buckets.has(s) else 1.0
	func lines(s: StringName) -> PackedStringArray:
		return buckets[s].lines if buckets.has(s) else PackedStringArray()

## Diminishing returns for speed-type increases. Identity near 0, asymptote SPEED_SOFTCAP.
static func soften(raw: float) -> float:
	if raw <= 0.0:
		return maxf(raw, -0.6)
	return raw / (1.0 + raw / SPEED_SOFTCAP)

const ADDITIVE_INCREASE := {
	&"stagger_power": true, &"projectile_damage": true, &"status_power": true,
	&"phys_damage": true, &"magic_damage": true, &"elemental_damage": true, &"damage": true, &"weapon_damage": true,
	&"heavy_damage": true, &"impact_damage": true, &"burn_damage": true, &"healing": true, &"buff_effect": true,
	&"valor_gain": true, &"xp_gain": true, &"magic_find": true, &"gold_find": true, &"projectile_speed": true,
}

static func is_additive_increase(k: StringName) -> bool:
	return ADDITIVE_INCREASE.has(k) or String(k).begins_with("dmg_")

static func armor_reduction(defense: float, attacker_level: int) -> float:
	if defense <= 0.0:
		return 0.0
	return defense / (defense + ARMOR_K_BASE + ARMOR_K_LEVEL * float(maxi(attacker_level, 1)))

## Compute every derived stat for a hero.
## attributes: base attribute totals before gear (class base + growth + allocated points).
static func compute(cls: ClassDef, level: int, attributes: Dictionary, modifiers: Array, loadout: WeaponLoadout) -> DerivedStats:
	var d := DerivedStats.new()
	d.level = level
	d.loadout = loadout if loadout != null else WeaponLoadout.new()
	var agg := Aggregate.new()
	for m in cls.class_modifiers:
		agg.add(m)
	for m in modifiers:
		var sm := m as StatModifier
		if sm == null:
			continue
		if String(sm.stat).begins_with("flag_"):
			var fk := StringName(String(sm.stat).substr(5))
			d.flags[fk] = d.flags.get(fk, 0.0) + sm.value
			continue
		agg.add(sm)

	# ---- Attributes ---------------------------------------------------------------------------------------
	var A := {}
	for a in BH.ATTRIBUTES:
		var base := float(attributes.get(a, 0))
		var v := floorf((base + agg.flat(a)) * (1.0 + agg.inc(a)) * agg.more(a))
		v = maxf(v, 0.0)
		A[a] = v
		var lines := PackedStringArray(["Base (class + level + points): %d" % roundi(base)])
		lines.append_array(agg.lines(a))
		d.set_stat(a, v, lines)
	var STR: float = A[&"str"]; var AGI: float = A[&"agi"]; var INT: float = A[&"int"]
	var WIS: float = A[&"wis"]; var SPI: float = A[&"spi"]; var DEX: float = A[&"dex"]
	var L := float(level)

	# ---- Pools --------------------------------------------------------------------------------------------
	_std(d, agg, &"max_hp", [
		["Class base", cls.base_hp], ["Level %d x %.0f" % [level, cls.hp_per_level], cls.hp_per_level * (L - 1.0)],
		["Strength %d x %.1f" % [STR, HP_PER_STR], STR * HP_PER_STR], ["Spirit %d x %.1f" % [SPI, HP_PER_SPI], SPI * HP_PER_SPI]], 1.0, INF, true)
	_std(d, agg, &"max_mana", [
		["Class base", cls.base_mana], ["Level %d x %.0f" % [level, cls.mana_per_level], cls.mana_per_level * (L - 1.0)],
		["Intelligence %d x %.1f" % [INT, MANA_PER_INT], INT * MANA_PER_INT], ["Wisdom %d x %.1f" % [WIS, MANA_PER_WIS], WIS * MANA_PER_WIS],
		["Spirit %d x %.1f" % [SPI, MANA_PER_SPI], SPI * MANA_PER_SPI]], 0.0, INF, true)
	_std(d, agg, &"hp_regen", [
		["Base", HP_REGEN_BASE], ["Spirit %d x %.2f" % [SPI, HP_REGEN_PER_SPI], SPI * HP_REGEN_PER_SPI],
		["Level %d x %.2f" % [level, HP_REGEN_PER_LEVEL], L * HP_REGEN_PER_LEVEL]], 0.0, INF)
	var mr_terms := [["Base", MANA_REGEN_BASE], ["Wisdom %d x %.2f" % [WIS, MANA_REGEN_PER_WIS], WIS * MANA_REGEN_PER_WIS],
		["Spirit %d x %.2f" % [SPI, MANA_REGEN_PER_SPI], SPI * MANA_REGEN_PER_SPI], ["Intelligence %d x %.2f" % [INT, MANA_REGEN_PER_INT], INT * MANA_REGEN_PER_INT]]
	_std(d, agg, &"mana_regen", mr_terms, 0.0, INF, false, cls.mana_regen_mult, "Class multiplier x%.2f" % cls.mana_regen_mult)

	# ---- Defense ------------------------------------------------------------------------------------------
	var def_more := 1.0
	var def_note := ""
	if d.loadout.dual_wield:
		def_more = 1.0 - WeaponLoadout.DUAL_DEFENSE_LESS
		def_note = "Dual wield stance: %d%% less" % roundi(WeaponLoadout.DUAL_DEFENSE_LESS * 100)
	_std(d, agg, &"defense", [["Class base", cls.base_defense], ["Strength %d x %.1f" % [STR, DEFENSE_PER_STR], STR * DEFENSE_PER_STR]],
		0.0, INF, true, def_more, def_note)
	var defense: float = d.get_stat(&"defense")
	var armor_dr := armor_reduction(defense, level)
	var pres := clampf(armor_dr + agg.flat(&"phys_res"), 0.0, RES_CAP)
	var pl := PackedStringArray(["Defense %d vs a level %d attacker: %.1f%%" % [roundi(defense), level, armor_dr * 100.0],
		"Formula: Defense / (Defense + %d + %d x attacker level)" % [ARMOR_K_BASE, ARMOR_K_LEVEL]])
	pl.append_array(agg.lines(&"phys_res"))
	pl.append("Cap %d%%" % roundi(RES_CAP * 100))
	d.set_stat(&"phys_res", pres, pl)
	d.set_stat(&"phys_res_flat", agg.flat(&"phys_res"))

	var res_cap := RES_CAP + agg.flat(&"res_cap")
	for e in Elements.ELEMENTAL:
		var rk := Elements.res_key(e)
		var all_flat := agg.flat(&"res_all")
		var v := WIS * RES_PER_WIS + agg.flat(rk) + all_flat
		var lines := PackedStringArray(["Wisdom %d x %.2f%%" % [WIS, RES_PER_WIS * 100.0]])
		if e == Elements.LIGHT or e == Elements.DARK:
			v += SPI * LIGHTDARK_RES_PER_SPI
			lines.append("Spirit %d x %.1f%%" % [SPI, LIGHTDARK_RES_PER_SPI * 100.0])
		lines.append_array(agg.lines(rk))
		lines.append_array(agg.lines(&"res_all"))
		lines.append("Cap %d%%, floor %d%%" % [roundi(res_cap * 100), roundi(RES_FLOOR * 100)])
		d.set_stat(rk, clampf(v, RES_FLOOR, res_cap), lines)

	# ---- Accuracy / evasion / crit ------------------------------------------------------------------------
	_std(d, agg, &"evasion", [["Agility %d x %.1f" % [AGI, EVASION_PER_AGI], AGI * EVASION_PER_AGI]], 0.0, INF, true)
	_std(d, agg, &"accuracy", [["Dexterity %d x %.1f" % [DEX, ACCURACY_PER_DEX], DEX * ACCURACY_PER_DEX],
		["Level %d x %.1f" % [level, ACCURACY_PER_LEVEL], L * ACCURACY_PER_LEVEL]], 1.0, INF, true)
	var wcrit := d.loadout.main_crit if not d.loadout.is_unarmed() else 0.05
	_std(d, agg, &"crit_chance", [["Weapon base", wcrit], ["Dexterity %d x %.2f%%" % [DEX, CRIT_PER_DEX * 100.0], DEX * CRIT_PER_DEX],
		["Agility %d x %.2f%%" % [AGI, CRIT_PER_AGI * 100.0], AGI * CRIT_PER_AGI]], 0.0, CRIT_CAP)
	var cd := maxf(1.0, CRIT_DAMAGE_BASE + agg.flat(&"crit_damage")) * agg.more(&"crit_damage")
	var cdl := PackedStringArray(["Base x%.2f" % CRIT_DAMAGE_BASE])
	cdl.append_array(agg.lines(&"crit_damage"))
	d.set_stat(&"crit_damage", cd, cdl)

	# ---- Weight ------------------------------------------------------------------------------------------
	var carried := maxf(0.0, agg.flat(&"carry_weight"))
	d.set_stat(&"carry_weight", carried, PackedStringArray(["Worn equipment and everything in the bag"]))
	var cap_l := PackedStringArray(["Base %d" % roundi(CARRY_BASE), "Strength %d x %.1f" % [STR, CARRY_PER_STR]])
	cap_l.append_array(agg.lines(&"carry_capacity"))
	var capacity := maxf(10.0, (CARRY_BASE + STR * CARRY_PER_STR + agg.flat(&"carry_capacity")) * (1.0 + agg.inc(&"carry_capacity")))
	d.set_stat(&"carry_capacity", capacity, cap_l)
	var load := carried / capacity
	d.set_stat(&"load", load, PackedStringArray(["%.1f / %.1f" % [carried, capacity],
		"Up to %d%%: no slowdown; %d%%: %d%% slower; 100%%+: Overburdened (%d%% slower, cannot dodge)" % [
			roundi(LOAD_FREE * 100), 100, roundi(LOAD_SLOW_MAX * 100), roundi(OVERBURDEN_SLOW * 100)]]))
	var load_mult := load_move_mult(load)
	if load >= 1.0:
		d.flags[&"overburdened"] = 1.0

	# ---- Speeds -------------------------------------------------------------------------------------------
	var ms_base := cls.base_move_speed
	var ms_inc := AGI * MOVE_PER_AGI + STR * MOVE_PER_STR + agg.inc(&"move_speed")
	var ms := (ms_base + agg.flat(&"move_speed")) * (1.0 + ms_inc) * agg.more(&"move_speed") * load_mult
	var ms_capped := clampf(ms, ms_base * MOVE_MIN_FACTOR, ms_base * MOVE_MAX_FACTOR)
	var msl := PackedStringArray(["Class base %.2f m/s" % ms_base, "Agility %d x %.2f%% = +%.1f%%" % [AGI, MOVE_PER_AGI * 100.0, AGI * MOVE_PER_AGI * 100.0],
		"Strength %d x %.2f%% = +%.1f%%" % [STR, MOVE_PER_STR * 100.0, STR * MOVE_PER_STR * 100.0]])
	msl.append_array(agg.lines(&"move_speed"))
	if load_mult < 1.0:
		msl.append("Load %d%%: %d%% slower%s" % [roundi(load * 100.0), roundi((1.0 - load_mult) * 100.0), "  — Overburdened" if load >= 1.0 else ""])
	msl.append("Maximum %.2f m/s (%d%% of base)%s" % [ms_base * MOVE_MAX_FACTOR, roundi(MOVE_MAX_FACTOR * 100), "  — capped" if ms > ms_capped else ""])
	d.set_stat(&"move_speed", ms_capped, msl)
	d.set_stat(&"move_speed_uncapped", ms)

	var as_more := agg.more(&"attack_speed")
	if d.loadout.dual_wield:
		as_more *= 1.0 + WeaponLoadout.DUAL_ATTACK_SPEED_MORE
	_speed(d, agg, &"attack_speed", [["Agility %d x %.1f%%" % [AGI, ATK_SPEED_PER_AGI * 100.0], AGI * ATK_SPEED_PER_AGI]], as_more,
		"Dual wield: %d%% more" % roundi(WeaponLoadout.DUAL_ATTACK_SPEED_MORE * 100) if d.loadout.dual_wield else "")
	_speed(d, agg, &"cast_speed", [["Agility %d x %.1f%%" % [AGI, CAST_SPEED_PER_AGI * 100.0], AGI * CAST_SPEED_PER_AGI],
		["Wisdom %d x %.2f%%" % [WIS, CAST_SPEED_PER_WIS * 100.0], WIS * CAST_SPEED_PER_WIS]], agg.more(&"cast_speed"), "")

	# ---- Blocking -----------------------------------------------------------------------------------------
	var bterms := []
	if d.loadout.has_shield:
		bterms.append(["Shield", d.loadout.shield_block])
		bterms.append(["Dexterity %d x %.1f%%" % [DEX, BLOCK_PER_DEX * 100.0], DEX * BLOCK_PER_DEX])
	_std(d, agg, &"block_chance", bterms, 0.0, BLOCK_CAP)
	var bs_base := d.loadout.shield_block_strength if d.loadout.has_shield else GUARD_BLOCK_STRENGTH
	_std(d, agg, &"block_strength", [["Shield" if d.loadout.has_shield else "Weapon guard", bs_base],
		["Strength %d x %.1f%%" % [STR, BLOCK_STR_PER_STR * 100.0], STR * BLOCK_STR_PER_STR]], 0.0, 1.0)

	# ---- Utility ------------------------------------------------------------------------------------------
	_std(d, agg, &"cdr", [["Wisdom %d x %.1f%%" % [WIS, CDR_PER_WIS * 100.0], WIS * CDR_PER_WIS]], 0.0, CDR_CAP)
	_std(d, agg, &"mana_cost_reduction", [["Wisdom %d x %.2f%%" % [WIS, MCR_PER_WIS * 100.0], WIS * MCR_PER_WIS]], -0.5, MCR_CAP)
	_std(d, agg, &"status_res", [["Spirit %d x %.1f%%" % [SPI, STATUS_RES_PER_SPI * 100.0], SPI * STATUS_RES_PER_SPI]], 0.0, STATUS_RES_CAP)
	_std(d, agg, &"knockback_res", [["Class base", cls.base_knockback_res], ["Strength %d x %.1f%%" % [STR, KB_RES_PER_STR * 100.0], STR * KB_RES_PER_STR]], 0.0, KB_RES_CAP)
	var wimpact := d.loadout.main_type.impact - 1.0 if d.loadout.main_type != null else 0.0
	_std(d, agg, &"impact_strength", [["Base", 1.0], ["Strength %d x %.1f%%" % [STR, IMPACT_PER_STR * 100.0], STR * IMPACT_PER_STR],
		["Weapon type", wimpact]], 0.1, INF)
	_std(d, agg, &"poise", [["Class base", cls.base_poise], ["Strength %d x %.1f" % [STR, POISE_PER_STR], STR * POISE_PER_STR]], 1.0, INF, true)
	var dcd := cls.dodge_cooldown * (1.0 - minf(DODGE_CDR_CAP, AGI * DODGE_CDR_PER_AGI)) + agg.flat(&"dodge_cooldown")
	d.set_stat(&"dodge_cooldown", maxf(0.3, dcd), PackedStringArray(["Class base %.1f s" % cls.dodge_cooldown,
		"Agility %d: -%.1f%% (max %d%%)" % [AGI, minf(DODGE_CDR_CAP, AGI * DODGE_CDR_PER_AGI) * 100.0, roundi(DODGE_CDR_CAP * 100)]]))

	# ---- Offense ------------------------------------------------------------------------------------------
	var sc_terms := []
	if d.loadout.main_type != null:
		for a in d.loadout.main_type.scaling:
			var coef: float = d.loadout.main_type.scaling[a]
			sc_terms.append(["%s %d x %.2f%% (%s scaling)" % [BH.ATTRIBUTE_NAMES[a], A[a], coef, d.loadout.main_type.display_name], A[a] * coef * 0.01])
		var mastery: float = cls.weapon_mastery.get(d.loadout.main_type.id, 0.0)
		if mastery != 0.0:
			sc_terms.append(["%s mastery" % cls.display_name, mastery])
	else:
		sc_terms.append(["Strength %d x 1%% (unarmed)" % STR, STR * 0.01])
	_std(d, agg, &"phys_damage", sc_terms, -0.9, INF)
	_std(d, agg, &"magic_damage", [["Intelligence %d x %.1f%%" % [INT, MAGIC_PER_INT * 100.0], INT * MAGIC_PER_INT],
		["Wisdom %d x %.1f%%" % [WIS, MAGIC_PER_WIS * 100.0], WIS * MAGIC_PER_WIS]], -0.9, INF)
	_std(d, agg, &"elemental_damage", [["Intelligence %d x %.1f%%" % [INT, ELEM_PER_INT * 100.0], INT * ELEM_PER_INT]], -0.9, INF)
	var pen_all := agg.flat(&"pen_elemental")
	d.set_stat(&"pen_elemental", pen_all, agg.lines(&"pen_elemental"))
	for e in Elements.ELEMENTAL:
		var dterms := []
		if e == Elements.LIGHT or e == Elements.DARK:
			dterms.append(["Spirit %d x %.2f%%" % [SPI, LIGHTDARK_PER_SPI * 100.0], SPI * LIGHTDARK_PER_SPI])
		_std(d, agg, Elements.dmg_key(e), dterms, -0.9, INF)
		_std(d, agg, Elements.pen_key(e), [["Elemental Penetration", pen_all]] if pen_all > 0.0 else [], 0.0, 1.0)
		_std(d, agg, StringName("added_" + String(Elements.key(e))), [], 0.0, INF)
	for wt in [&"sword", &"greatsword", &"axe", &"greataxe", &"spear", &"javelin", &"club", &"dagger", &"claw", &"knuckles", &"bow", &"staff", &"wand"]:
		if agg.buckets.has(StringName("dmg_wt_" + String(wt))):
			_std(d, agg, StringName("dmg_wt_" + String(wt)), [], -0.9, INF)
	for k in [&"damage", &"weapon_damage", &"heavy_damage", &"impact_damage", &"burn_damage", &"pen_armor", &"life_leech",
			&"mana_leech", &"mana_on_hit", &"valor_gain", &"xp_gain", &"magic_find", &"gold_find", &"added_physical", &"status_power"]:
		_std(d, agg, k, [], -0.9 if k != &"pen_armor" else 0.0, INF)
	_std(d, agg, &"stagger_power", [["Strength %d x %.1f%%" % [STR, STAGGER_PER_STR * 100.0], STR * STAGGER_PER_STR]], -0.9, INF)
	_std(d, agg, &"projectile_damage", [["Dexterity %d x %.1f%%" % [DEX, PROJ_DMG_PER_DEX * 100.0], DEX * PROJ_DMG_PER_DEX]], -0.9, INF)
	_std(d, agg, &"healing", [["Spirit %d x %.1f%%" % [SPI, HEAL_PER_SPI * 100.0], SPI * HEAL_PER_SPI]], -0.9, INF)
	_std(d, agg, &"buff_effect", [["Wisdom %d x %.1f%%" % [WIS, BUFF_PER_WIS * 100.0], WIS * BUFF_PER_WIS],
		["Spirit %d x %.1f%%" % [SPI, BUFF_PER_SPI * 100.0], SPI * BUFF_PER_SPI]], -0.9, INF)
	_std(d, agg, &"projectile_speed", [["Dexterity %d x %.1f%%" % [DEX, PROJ_SPEED_PER_DEX * 100.0], DEX * PROJ_SPEED_PER_DEX]], -0.5, 2.0)
	_std(d, agg, &"skill_levels", [], 0.0, 5.0, true)
	var dodge_inc := minf(DODGE_DIST_CAP, AGI * DODGE_DIST_PER_AGI) + agg.inc(&"dodge_distance")
	d.set_stat(&"dodge_distance", dodge_inc, PackedStringArray(["Agility %d x %.2f%% (max %d%%)" % [AGI, DODGE_DIST_PER_AGI * 100.0, roundi(DODGE_DIST_CAP * 100)]]))
	var pw := minf(PARRY_MAX, PARRY_BASE + DEX * PARRY_PER_DEX + agg.flat(&"parry_window"))
	d.set_stat(&"parry_window", pw, PackedStringArray(["Base %.2f s" % PARRY_BASE, "Dexterity %d x %.1f ms" % [DEX, PARRY_PER_DEX * 1000.0],
		"Maximum %.2f s" % PARRY_MAX]))
	# Global damage multipliers from buffs/debuffs (Weakened, Empowered, Overcharged, Fortified ...).
	var od := agg.more(&"outgoing_damage") * (1.0 + agg.inc(&"outgoing_damage"))
	d.set_stat(&"outgoing_damage", maxf(0.05, od), agg.lines(&"outgoing_damage"))
	var dt := agg.more(&"damage_taken") * (1.0 + agg.inc(&"damage_taken"))
	d.set_stat(&"damage_taken", maxf(0.05, dt), agg.lines(&"damage_taken"))
	# Readable chances for the character sheet (same formulas as the damage pipeline, vs a same-level reference foe).
	var ref_eva := DEFAULT_ENEMY_EVASION_PER_LEVEL * L + 6.0
	var acc: float = d.get_stat(&"accuracy")
	d.set_stat(&"accuracy_chance", 1.0 - minf(DamagePipeline.EVADE_CAP, ref_eva / (ref_eva + acc * DamagePipeline.EVADE_ACC_FACTOR)),
		PackedStringArray(["Against a level %d enemy with %d Evasion" % [level, roundi(ref_eva)],
		"Formula: 1 - Evasion / (Evasion + Accuracy x %d)" % roundi(DamagePipeline.EVADE_ACC_FACTOR)]))
	var eva: float = d.get_stat(&"evasion")
	var ref_acc := ACCURACY_PER_LEVEL * L * 4.0 + 20.0
	d.set_stat(&"evade_chance", minf(DamagePipeline.EVADE_CAP, eva / (eva + ref_acc * DamagePipeline.EVADE_ACC_FACTOR)) if eva > 0.0 else 0.0,
		PackedStringArray(["Against a level %d enemy with %d Accuracy" % [level, roundi(ref_acc)], "Cap %d%%" % roundi(DamagePipeline.EVADE_CAP * 100)]))
	d.set_stat(&"physical_armor_dr", armor_dr, PackedStringArray(["Defense / (Defense + %d + %d x level)" % [ARMOR_K_BASE, ARMOR_K_LEVEL]]))
	_std(d, agg, &"arcane_max", [["Base", 5.0]], 0.0, 10.0, true)

	# Weapon damage ranges shown on the character sheet (same function the pipeline uses for base rolls).
	var rng_main := weapon_range(d, 0)
	d.set_stat(&"weapon_min", rng_main.x)
	d.set_stat(&"weapon_max", rng_main.y)
	if d.loadout.dual_wield:
		var rng_off := weapon_range(d, 1)
		d.set_stat(&"off_min", rng_off.x)
		d.set_stat(&"off_max", rng_off.y)
	var aps := d.loadout.aps() * d.get_stat(&"attack_speed")
	d.set_stat(&"attacks_per_second", aps)
	return d

## Movement multiplier from load (carried / capacity).
static func load_move_mult(load: float) -> float:
	if load >= 1.0:
		return 1.0 - OVERBURDEN_SLOW
	if load <= LOAD_FREE:
		return 1.0
	return 1.0 - LOAD_SLOW_MAX * (load - LOAD_FREE) / (1.0 - LOAD_FREE)

## Displayed and rolled weapon base range for one hand after flat added physical damage (before % bonuses).
static func weapon_range(d: DerivedStats, hand: int) -> Vector2:
	var lo := UNARMED_MIN
	var hi := UNARMED_MAX
	if not d.loadout.is_unarmed():
		var r := d.loadout.damage_range(hand)
		lo = r.x
		hi = r.y
	var add := d.get_stat(&"added_physical")
	if d.loadout.dual_wield:
		lo *= WeaponLoadout.DUAL_DAMAGE_PER_HAND
		hi *= WeaponLoadout.DUAL_DAMAGE_PER_HAND
	return Vector2(lo + add * 0.8, hi + add * 1.2)

# Generic: (sum of terms + flat) * (1 + inc) * more * extra_more, clamped.
static func _std(d: DerivedStats, agg: Aggregate, k: StringName, terms: Array, lo: float, hi: float, round_down := false,
		extra_more := 1.0, extra_note := "") -> void:
	var base := 0.0
	var lines := PackedStringArray()
	for t in terms:
		base += float(t[1])
		if absf(float(t[1])) > 0.00001:
			lines.append("%s: %s" % [t[0], StatDefs.format_value(k, float(t[1])) if StatDefs.fmt_of(k) != StatDefs.Fmt.MULT else "%+.2f" % float(t[1])])
	lines.append_array(agg.lines(k))
	var v: float
	if is_additive_increase(k):
		# "Increased X" stats are themselves percentages: INC modifiers add to them rather than scale them.
		v = (base + agg.flat(k) + agg.inc(k)) * agg.more(k) * extra_more
	else:
		v = (base + agg.flat(k)) * (1.0 + agg.inc(k)) * agg.more(k) * extra_more
	if extra_note != "":
		lines.append(extra_note)
	if round_down:
		v = floorf(v)
	var capped := clampf(v, lo, hi)
	if hi < INF and v > hi:
		lines.append("Capped at %s" % StatDefs.format_value(k, hi))
	d.set_stat(k, capped, lines)

static func _speed(d: DerivedStats, agg: Aggregate, k: StringName, terms: Array, more: float, note: String) -> void:
	var raw := agg.inc(k) + agg.flat(k)
	var lines := PackedStringArray()
	for t in terms:
		raw += float(t[1])
		lines.append("%s: +%.1f%%" % [t[0], float(t[1]) * 100.0])
	lines.append_array(agg.lines(k))
	var eff := soften(raw)
	lines.append("Total increase %+.1f%% -> %+.1f%% after diminishing returns" % [raw * 100.0, eff * 100.0])
	if note != "":
		lines.append(note)
	var v := (1.0 + eff) * more
	var capped := clampf(v, SPEED_MULT_MIN, SPEED_MULT_MAX)
	if v > capped:
		lines.append("Capped at x%.2f" % SPEED_MULT_MAX)
	d.set_stat(k, capped, lines)
