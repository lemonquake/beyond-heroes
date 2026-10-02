extends Node
## bh-033 gear balance sheet: seeded distributions of generated equipment and full-set stacking.
##   godot --headless --path game res://tests/tools/gear_balance_sheet.tscn -- --out=<dir> [--n=300]
## Writes <dir>/gear_sheet.json and <dir>/gear_sheet.md. Run it before and after a generator change; the seeds are fixed,
## so the two sheets compare like for like.

const CATS := [&"weapon", &"shield", &"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots", &"accessory"]
const LEVELS := [5, 15, 30, 50]
const RARITIES := [BH.Rarity.BASIC, BH.Rarity.ADVANCED, BH.Rarity.LICENSED, BH.Rarity.ELITE, BH.Rarity.MASTER,
	BH.Rarity.MYTHICAL, BH.Rarity.LEGENDARY, BH.Rarity.AETHER]
const RANGED := [&"bow", &"crossbow", &"javelin"]
const SUPPORT := [&"max_mana", &"mana_regen", &"mana_leech", &"hp_regen", &"healing", &"magic_find", &"move_speed", &"cdr", &"max_hp"]

var out_dir := "user://gear_sheet"
var n := 300
var _gen: Object = ItemGenerator.new()

func _ready() -> void:
	Game.save_slot = 97
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--n="):
			n = int(a.substr(4))
	DirAccess.make_dir_recursive_absolute(out_dir)
	var sheet := {"generator": _generator_tag(), "per_item": _per_item(), "full_set": _full_sets(), "examples": _examples()}
	var f := FileAccess.open(out_dir.path_join("gear_sheet.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(sheet, "  "))
	f.close()
	var md := FileAccess.open(out_dir.path_join("gear_sheet.md"), FileAccess.WRITE)
	md.store_string(_markdown(sheet))
	md.close()
	print("GEAR_SHEET written to ", out_dir)
	get_tree().quit()

func _generator_tag() -> String:
	return "bh-033" if _gen.has_method("affix_family") else "pre-bh-033"

## Whether an affix on a weapon is relevant to that weapon (the same test before and after the change).
func weapon_affix_relevant(it: ItemInstance, stat: StringName) -> bool:
	var s := String(stat)
	if s.begins_with("dmg_"):
		var e := Elements.from_key(StringName(s.substr(4)))
		if e == it.base.element:
			return true
		for a in it.affixes:
			var d := DB.affix(StringName(a.id))
			if d != null and String(d.stat) == "added_" + s.substr(4):
				return true
		return false
	if s.begins_with("pen_") and s != "pen_armor" and s != "pen_elemental":
		return weapon_affix_relevant(it, StringName("dmg_" + s.substr(4)))
	if stat == &"projectile_damage":
		return it.base.weapon_type in RANGED
	return true

func _strength(it: ItemInstance) -> float:
	var t := 0.0
	for a in it.affixes:
		var d := DB.affix(StringName(a.id))
		if d == null:
			continue
		var top := float(d.tiers[d.tiers.size() - 1][2])
		t += absf(float(a.value)) / maxf(absf(top), 0.0001) * (float(_gen.call("affix_cost", d)) if _gen.has_method("affix_cost") else 1.0)
	return t

func _per_item() -> Array:
	var rows := []
	for cat in CATS:
		for lv in LEVELS:
			for rar in RARITIES:
				var rng := RandomNumberGenerator.new()
				rng.seed = hash("%s/%d/%d" % [cat, lv, rar])
				var count := 0
				var affix_total := 0
				var res3 := 0
				var res_all_mix := 0
				var max_res := 0
				var irrelevant := 0
				var filler := 0
				var no_offense := 0
				var strength := 0.0
				var strength_max := 0.0
				for i in n:
					var base := ItemGenerator.random_base(rng, lv, [cat], &"", 0.0)
					if base == null:
						continue
					var r2 := RandomNumberGenerator.new()
					r2.seed = rng.randi()
					var it := ItemGenerator.generate(base, lv, rar, r2)
					count += 1
					affix_total += it.affixes.size()
					var res := 0
					var has_all := false
					var support := 0
					var offense := 0
					for a in it.affixes:
						var d := DB.affix(StringName(a.id))
						if d == null:
							continue
						var s := String(d.stat)
						if s == "res_all":
							has_all = true
						elif s.begins_with("res_"):
							res += 1
						if cat == &"weapon":
							if not weapon_affix_relevant(it, d.stat):
								irrelevant += 1
							if d.stat in SUPPORT:
								support += 1
							elif not s in ["str", "agi", "int", "wis", "spi", "dex"]:
								offense += 1
					if res >= 3:
						res3 += 1
					if has_all and res > 0:
						res_all_mix += 1
					max_res = maxi(max_res, res + (1 if has_all else 0))
					if support > 1:
						filler += 1
					if cat == &"weapon" and not it.affixes.is_empty() and offense == 0:
						no_offense += 1
					var st := _strength(it)
					strength += st
					strength_max = maxf(strength_max, st)
				if count == 0:
					continue
				rows.append({"category": String(cat), "ilvl": lv, "rarity": BH.RARITY_NAMES[rar], "items": count,
					"avg_affixes": snappedf(float(affix_total) / count, 0.01),
					"res3_pct": snappedf(100.0 * res3 / count, 0.1), "res_all_mixed_pct": snappedf(100.0 * res_all_mix / count, 0.1),
					"max_res_effects": max_res, "irrelevant_weapon_affixes_per_item": snappedf(float(irrelevant) / count, 0.01),
					"weapon_filler_pct": snappedf(100.0 * filler / count, 0.1), "weapon_no_offense_pct": snappedf(100.0 * no_offense / count, 0.1),
					"avg_strength": snappedf(strength / count, 0.01), "max_strength": snappedf(strength_max, 0.01)})
	return rows

func _hero(cid: StringName, level: int, rarity: int, seed_value: int, crystals := false) -> HeroData:
	var h := Game.new_hero(cid, "Gear sheet")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	h.progress.allocate(&"int" if cid == &"mage" else (&"dex" if cid == &"ranger" else &"str"), h.progress.free_points)
	h.equipment.tier_rank = 8
	for slot in BH.SLOTS:
		if slot == &"main_weapon" or (slot == &"sub_weapon" and cid != &"knight"):
			continue
		var cat := StringName(String(slot).split("_")[0]) if slot != &"inner_garment" else slot
		if slot == &"sub_weapon":
			cat = &"shield"
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("%s/%d/%s" % [cid, seed_value, slot])
		var base := ItemGenerator.random_base(rng, level, [cat], cid, 1.0)
		if base == null:
			continue
		var r2 := RandomNumberGenerator.new()
		r2.seed = rng.randi()
		var it := ItemGenerator.generate(base, level, rarity, r2)
		if crystals:
			it.sockets = Sockets.max_sockets(it)
			it.gems.clear()
			for i in it.sockets:
				it.gems.append("sora_orbital")
		h.equipment.slots[slot] = it
	return h

func _full_sets() -> Dictionary:
	var out := {}
	for scenario in ["legendary_l50", "aether_l50_res_crystals", "elite_l30"]:
		var rar := BH.Rarity.LEGENDARY if scenario == "legendary_l50" else (BH.Rarity.AETHER if scenario.begins_with("aether") else BH.Rarity.ELITE)
		var lv := 30 if scenario == "elite_l30" else 50
		var capped := 0
		var total := 0
		var res_sum := 0.0
		var res_max := 0.0
		var hp_sum := 0.0
		var def_sum := 0.0
		for cid in [&"knight", &"mage", &"ranger", &"shadowblade"]:
			for s in 25:
				var h := _hero(cid, lv, rar, s, scenario.ends_with("crystals"))
				var d := h.compute_stats()
				for e in Elements.ELEMENTAL:
					var v := d.get_stat(Elements.res_key(e))
					total += 1
					res_sum += v
					res_max = maxf(res_max, v)
					if v >= StatCalculator.RES_CAP - 0.001:
						capped += 1
				hp_sum += d.get_stat(&"max_hp")
				def_sum += d.get_stat(&"phys_res")
		out[scenario] = {"elements_at_cap_pct": snappedf(100.0 * capped / maxi(total, 1), 0.1),
			"avg_elemental_res_pct": snappedf(100.0 * res_sum / maxi(total, 1), 0.1), "max_elemental_res_pct": snappedf(100.0 * res_max, 0.1),
			"avg_max_hp": roundi(hp_sum / 100.0), "avg_phys_res_pct": snappedf(100.0 * def_sum / 100.0, 0.1)}
	return out

func _describe(it: ItemInstance) -> Dictionary:
	var lines := []
	for l in it.affix_lines():
		lines.append(l)
	return {"name": it.display_name(), "base": String(it.base.id), "rarity": it.rarity_name(), "ilvl": it.ilvl, "affixes": lines,
		"damage": [snappedf(it.damage_range().x, 0.1), snappedf(it.damage_range().y, 0.1)] if it.base.is_weapon() else [],
		"defense": snappedf(it.defense_value(), 0.1) if not it.base.is_weapon() else 0.0, "strength": snappedf(_strength(it), 0.01)}

func _examples() -> Array:
	var out := []
	for spec in [[&"guardian_plate_like", &"armor"], [&"x", &"helm"], [&"x", &"boots"], [&"x", &"weapon"], [&"x", &"accessory"]]:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("example/%s" % spec[1])
		for rar in [BH.Rarity.ELITE, BH.Rarity.LEGENDARY]:
			var base := ItemGenerator.random_base(rng, 40, [spec[1]], &"", 0.0)
			var r2 := RandomNumberGenerator.new()
			r2.seed = 7700 + rar
			out.append(_describe(ItemGenerator.generate(base, 40, rar, r2)))
	return out

func _markdown(sheet: Dictionary) -> String:
	var s := "# Gear balance sheet (%s)\n\n%d items per row, fixed seeds.\n\n" % [sheet.generator, n]
	s += "## Full equipment sets (100 heroes per scenario: four classes x 25 seeds)\n\n| Scenario | Elements at 75%% cap | Avg elemental res | Max | Avg max HP | Avg phys res |\n| --- | --- | --- | --- | --- | --- |\n"
	for k in sheet.full_set:
		var r: Dictionary = sheet.full_set[k]
		s += "| %s | %s%% | %s%% | %s%% | %d | %s%% |\n" % [k, r.elements_at_cap_pct, r.avg_elemental_res_pct, r.max_elemental_res_pct, r.avg_max_hp, r.avg_phys_res_pct]
	s += "\n## Per item (level 50 rows; JSON has every level)\n\n| Category | Rarity | Affixes | >=3 res | all+single res | max res effects | irrelevant/weapon | weapon >1 support | weapon no offense | avg strength | max strength |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
	for r in sheet.per_item:
		if int(r.ilvl) != 50:
			continue
		s += "| %s | %s | %s | %s%% | %s%% | %s | %s | %s%% | %s%% | %s | %s |\n" % [r.category, r.rarity, r.avg_affixes, r.res3_pct, r.res_all_mixed_pct,
			r.max_res_effects, r.irrelevant_weapon_affixes_per_item, r.weapon_filler_pct, r.weapon_no_offense_pct, r.avg_strength, r.max_strength]
	s += "\n## Examples (item level 40)\n\n"
	for e in sheet.examples:
		s += "- **%s** (%s, %s)%s: %s\n" % [e.name, e.rarity, e.base, (" damage %s-%s" % [e.damage[0], e.damage[1]]) if not e.damage.is_empty() else (" defense %s" % e.defense), "; ".join(e.affixes)]
	return s
