class_name ItemGenerator
## Rolls rarity, affixes, licenses and powers. Rarity raises the number of enchantments, their tier quality and unlocks
## special properties — it never multiplies base stats beyond a small quality roll (Aether is not "+10000% damage").
##
## Tier rules (see RULES): affix count, tier bias, minimum roll, maximum base quality, powers.
##   Beginner   starter gear only, no enchantments
##   Common     no enchantments
##   Basic      1 enchantment                              Advanced  2 enchantments
##   Licensed   2-3 enchantments + a faction license bonus  Elite     3-4, biased to the top tiers
##   Master     4, masterwork base quality, one perfected enchantment
##   Mythical   4-5 + one mythical power                   Legendary 5 + one legendary (build-defining) power
##   Aether     5-6 top tier + one legendary power + one Aether power (alters an ability)
##   Cosmic, Divine, Eternal, Primordial (bh-034, DataAscendant): 6-7 top-tier enchantments at their highest rolls, a
##              legendary and an Aether power, the tier's signature power and a set; only the Ascendant collections
##              carry these rarities and only dungeon bosses of level 70+ drop them

# [min affixes, max affixes, tier bias (0 uniform, 1 upper half, 2 top only), min value roll, min quality, max quality]
const RULES := [
	[0, 0, 0, 0.0, 0.0, 0.0],      # Beginner
	[0, 0, 0, 0.0, 0.0, 0.03],     # Common
	[1, 1, 0, 0.0, 0.0, 0.05],     # Basic
	[2, 2, 0, 0.0, 0.0, 0.07],     # Advanced
	[2, 3, 0, 0.1, 0.02, 0.08],    # Licensed
	[3, 4, 1, 0.2, 0.03, 0.10],    # Elite
	[4, 4, 1, 0.35, 0.10, 0.15],   # Master
	[4, 5, 1, 0.45, 0.08, 0.15],   # Mythical
	[5, 5, 2, 0.55, 0.10, 0.18],   # Legendary
	[5, 6, 2, 0.70, 0.12, 0.20],   # Aether
	[6, 6, 2, 0.78, 0.14, 0.22],   # Cosmic
	[6, 6, 2, 0.84, 0.16, 0.24],   # Divine
	[6, 7, 2, 0.90, 0.18, 0.26],   # Eternal
	[7, 7, 2, 0.95, 0.20, 0.30],   # Primordial
]
# Relative drop weights at 0% magic find (Beginner never drops from monsters).
const WEIGHTS := [0.0, 520.0, 250.0, 130.0, 55.0, 28.0, 11.0, 4.0, 1.6, 0.25, 0.0, 0.0, 0.0, 0.0]   # Ascendant: never rolled
# Minimum item level for a tier to drop at all (keeps the first minutes of the game grounded).
const MIN_ILVL := [1, 1, 1, 1, 2, 3, 4, 5, 6, 8, 70, 80, 90, 100]

const RARE_NAME_A := ["Grim", "Ash", "Dusk", "Iron", "Blood", "Storm", "Hollow", "Rune", "Gloom", "Ember", "Raven", "Bone",
	"Frost", "Doom", "Sorrow", "Night", "Warden", "Oath", "Wraith", "Thorn"]
const RARE_NAME_B := ["Bite", "Ward", "Song", "Brand", "Veil", "Fang", "Mark", "Shroud", "Grasp", "Heart", "Coil", "Crown",
	"Edge", "Tongue", "Spire", "Wake", "Gaze", "Hold", "Vow", "Stride"]

## Rarity roll. magic_find (fraction) and rank_bonus (elites 0.5, bosses 1.5) shift weight toward higher tiers.
static func roll_rarity(rng: RandomNumberGenerator, magic_find := 0.0, rank_bonus := 0.0, ilvl := 99) -> int:
	var w := WEIGHTS.duplicate()
	var mf := maxf(0.0, magic_find)
	var boost := 1.0 + mf / (1.0 + mf * 0.5) + rank_bonus
	for i in range(1, w.size()):
		w[i] *= pow(boost, 0.35 + 0.16 * i)
		if ilvl < MIN_ILVL[i]:
			w[i] = 0.0
	var total := 0.0
	for x in w:
		total += x
	var r := rng.randf() * total
	for i in w.size():
		r -= w[i]
		if r <= 0.0 and w[i] > 0.0:
			return i
	return BH.Rarity.COMMON

## `force`: the rarity is exactly `rarity`, whatever the base (the Debug console's Item Summoner): a fixed-rarity unique or
## set piece takes it too, and a plain base may be Cosmic .. Primordial, carrying that tier's signature power.
static func generate(base: ItemBaseDef, ilvl: int, rarity: int, rng: RandomNumberGenerator, force := false) -> ItemInstance:
	var it := ItemInstance.new()
	it.base = base
	it.ilvl = maxi(1, ilvl)
	it.seed_value = rng.seed
	if not BH.CATEGORY_SLOTS.has(base.category):
		# bh-018: crystals keep their grade's colour tier; everything else in the bag is Common
		it.rarity = base.fixed_rarity if base.category == &"crystal" and base.fixed_rarity >= 0 else BH.Rarity.COMMON
		return it
	if force:
		pass
	elif base.fixed_rarity >= 0:
		rarity = base.fixed_rarity
	elif base.set_id != &"":
		rarity = maxi(rarity, BH.Rarity.MASTER)
	rarity = clampi(rarity, 0, BH.RARITY_COUNT - 1)
	# the Ascendant rarities belong to the Ascendant collections (and the Fabled Arms) only: a drop never makes a
	# Cosmic sword of a plain base. Only the Item Summoner forces one.
	if rarity >= BH.Rarity.COSMIC and base.fixed_rarity < BH.Rarity.COSMIC and not force:
		rarity = BH.Rarity.AETHER
	it.rarity = rarity
	var rule: Array = RULES[rarity]
	it.quality = snappedf(rng.randf_range(float(rule[4]), float(rule[5])), 0.01)
	var n := rng.randi_range(rule[0], rule[1])
	_roll_affixes(it, n, int(rule[2]), float(rule[3]), rng)
	if rarity == BH.Rarity.MASTER and not it.affixes.is_empty():
		_perfect_one(it, rng)
	if rarity == BH.Rarity.LICENSED:
		it.license = _pick_license(base, rng)
	for pid in base.fixed_powers:
		it.powers.append(String(pid))
	if force and DataAscendant.TIER.has(rarity):
		var sig := String(DataAscendant.TIER[rarity].power)
		if not it.powers.has(sig):
			it.powers.append(sig)
	match rarity:
		BH.Rarity.MYTHICAL:
			_add_power(it, &"mythical", rng)
		BH.Rarity.LEGENDARY:
			_add_power(it, &"legendary", rng)
		BH.Rarity.AETHER, BH.Rarity.COSMIC, BH.Rarity.DIVINE, BH.Rarity.ETERNAL, BH.Rarity.PRIMORDIAL:
			_add_power(it, &"legendary", rng)
			_add_power(it, &"aether", rng)
	# bh-012: a relic power — a signature utility passive — on some Licensed-or-better pieces
	if rarity >= BH.Rarity.LICENSED and base.unique_name == "" and rng.randf() < RELIC_CHANCE[clampi(rarity - BH.Rarity.LICENSED, 0, RELIC_CHANCE.size() - 1)]:
		_add_power(it, &"relic", rng)
	it.custom_name = _name_for(it, rng)
	if it.custom_name == "" and rarity >= ItemNames.MIN_RARITY and base.unique_name == "" and base.set_id == &"":
		var nm := ItemNames.roll(it, rng)
		it.custom_name = nm[0]
		it.epithet = nm[1]
	_forge_weapon_name(it)
	_roll_sockets(it)
	return it

## bh-018: now and then a piece is found with a socket or two already open (never more than half its tier maximum).
## Drawn from the item's own seed, like the forged name, so it never moves the main roll sequence.
static func _roll_sockets(it: ItemInstance) -> void:
	if it.rarity <= BH.Rarity.BEGINNER or it.base.unique_name != "":
		return
	var r := RandomNumberGenerator.new()
	r.seed = hash("%d/%s/sockets" % [it.seed_value, it.base.id])
	if r.randf() >= 0.06 + 0.015 * float(it.rarity):
		return
	var cap := maxi(1, Sockets.max_sockets(it) / 2)
	it.sockets = r.randi_range(1, cap)
	it.gems.clear()
	for i in it.sockets:
		it.gems.append("")

## bh-015: a Common, Basic or Advanced weapon gets a forged prefix and/or suffix (NameForge) — "Saltworn Shortbow",
## "Emberkissed Hornbow of the Grey Ferry" — so two drops of one base rarely read the same. Where an enchantment
## already names a side ("Flaming", "of Precision") it keeps it. Drawn from the item's own seed, so it neither moves
## the main roll sequence nor changes when the item is loaded.
static func _forge_weapon_name(it: ItemInstance) -> void:
	var b := it.base
	if not b.is_weapon() or it.custom_name != "" or b.unique_name != "" or b.set_id != &"" 			or it.rarity < BH.Rarity.COMMON or it.rarity > BH.Rarity.ADVANCED:
		return
	var r := RandomNumberGenerator.new()
	r.seed = hash("%d/%s/name" % [it.seed_value, b.id])
	var has_pre := false
	var has_suf := false
	for a in it.affixes:
		var d := DB.affix(StringName(a.id))
		if d:
			has_pre = has_pre or d.is_prefix
			has_suf = has_suf or not d.is_prefix
	match it.rarity:
		BH.Rarity.COMMON:
			# plain steel: one forged word, before or after
			if r.randf() < 0.65:
				it.name_prefix = NameForge.weapon_prefix(b.element, r)
			else:
				it.name_suffix = NameForge.weapon_suffix(r)
		_:
			if not has_pre and r.randf() < 0.85:
				it.name_prefix = NameForge.weapon_prefix(b.element, r)
			if not has_suf and r.randf() < 0.75:
				it.name_suffix = NameForge.weapon_suffix(r)

## Chance of a relic power by rarity from Licensed up (Licensed, Elite, Master, Mythical, Legendary, Aether, then the
## four Ascendant tiers).
const RELIC_CHANCE := [0.15, 0.3, 0.45, 0.6, 0.6, 0.6, 0.7, 0.75, 0.8, 0.9]

## The gear inside a Relic Cache of `tier` (DataRelics.CACHES) opened by a hero of `level`: one piece at least the
## cache's floor rarity, the rest rolled with a strong rarity bonus; a Radiant cache has a small chance of more.
static func relic_items(tier: int, level: int, rng: RandomNumberGenerator, magic_find := 0.0, class_hint := &"") -> Array:
	var c: Dictionary = DataRelics.CACHES[clampi(tier, 0, DataRelics.CACHES.size() - 1)]
	var ilvl := clampi(level + int(c.ilvl), 1, BH.LEVEL_CAP + 5)
	var out := []
	for i in int(c.items):
		var rarity := maxi(roll_rarity(rng, magic_find, float(c.bonus), ilvl), int(c.min))
		if i == 0:
			rarity = maxi(rarity, int(c.floor))
		if tier == 2 and i == 1 and rng.randf() < 0.25:
			rarity = maxi(rarity, BH.Rarity.LEGENDARY)
		var base := random_base(rng, ilvl, [], class_hint)
		if base == null:
			continue
		var r2 := RandomNumberGenerator.new()
		r2.seed = rng.randi()
		out.append(generate(base, ilvl, rarity, r2))
	if tier >= 1 and rng.randf() < (0.06 if tier == 1 else 0.18):
		var sb := random_special(rng, ilvl + 4, rng.randf() < 0.6, class_hint)
		if sb:
			var r3 := RandomNumberGenerator.new()
			r3.seed = rng.randi()
			out.append(generate(sb, ilvl, BH.Rarity.MASTER if sb.set_id != &"" else BH.Rarity.AETHER, r3))
	return out

static func _roll_affixes(it: ItemInstance, n: int, bias: int, min_roll: float, rng: RandomNumberGenerator) -> void:
	var pool: Array = []
	for a in DB.affixes_for(it.base.category):
		if it.rarity >= a.min_rarity and affix_fits(it.base, a):
			pool.append(a)
	var used_groups := {}
	var attempts := 0
	while it.affixes.size() < n and attempts < 64:
		attempts += 1
		# bh-033: only affixes the piece's identity still has room for; a weapon's first enchantment is offensive.
		var open := pool.filter(func(c): return can_add(it, c) and (not it.base.is_weapon() or not it.affixes.is_empty() or affix_family(c) == &"offense"))
		var a := _weighted_pick(open, rng, used_groups)
		if a == null:
			break
		var tiers := a.allowed_tiers(it.ilvl)
		if tiers.is_empty():
			used_groups[a.group] = true
			continue
		var tier: int
		match bias:
			0: tier = tiers[rng.randi_range(0, tiers.size() - 1)]
			1: tier = tiers[maxi(0, tiers.size() - 1 - rng.randi_range(0, 1))]
			_: tier = tiers[tiers.size() - 1]
		var t: Array = a.tiers[tier]
		var roll := rng.randf_range(min_roll, 1.0)
		var v := lerpf(float(t[1]), float(t[2]), roll)
		v = roundf(v) if a.integer else snappedf(v, 0.001)
		it.affixes.append({"id": String(a.id), "tier": tier, "value": v})
		used_groups[a.group] = true
	_fit_budget(it)

# ---- bh-033: coherent equipment identities ---------------------------------------------------------------------------
## Every affix belongs to one family. A piece's category limits how many affix slots of each family it may carry, so an
## armour roll cannot be four resistances and a weapon roll cannot be mostly mana and regeneration. Families missing from
## a category's row are unlimited (weapons: offense; armour: defense). See docs/GEAR_BALANCE.md.
const FAMILY_STATS := {
	&"defense": [&"local_def", &"local_def_flat", &"max_hp", &"evasion", &"block_chance", &"knockback_res", &"status_res", &"thorns"],
	&"attribute": [&"str", &"agi", &"int", &"wis", &"spi", &"dex"],
	&"support": [&"max_mana", &"mana_regen", &"hp_regen", &"healing", &"move_speed", &"cdr", &"life_leech", &"mana_leech",
		&"hp_on_kill", &"mana_on_kill", &"potion_power"],
	&"fortune": [&"magic_find", &"gold_find", &"xp_gain", &"ember_find"],
}
const FAMILY_LIMITS := {
	&"weapon": {&"resist": 0, &"attribute": 2, &"support": 1, &"fortune": 0, &"defense": 0},
	&"gloves": {&"resist": 2, &"attribute": 2, &"offense": 2, &"support": 2, &"fortune": 1},
	&"helm": {&"resist": 2, &"attribute": 2, &"offense": 2, &"support": 2, &"fortune": 1},
	&"accessory": {&"resist": 2, &"attribute": 2, &"offense": 3, &"support": 2, &"fortune": 1},
	&"_armour": {&"resist": 2, &"attribute": 2, &"offense": 1, &"support": 2, &"fortune": 1},
}
## All Resistances fills both resistance slots, so it never shares a piece with a single-element resistance.
const WIDE_AFFIXES := {&"res_all": 2}
## Strength cost of a full-value roll (1.0 = an ordinary affix at the top of its best tier).
const AFFIX_COST := {&"res_all": 2.0, &"skill_levels": 2.0}
## Total affix strength a piece may carry by rarity (sum of cost x value / best value). Rolls above it are pulled down
## toward their tier minimum; a masterwork enchantment is never reduced.
const RARITY_BUDGET := [0.0, 0.0, 1.0, 2.0, 2.6, 3.5, 4.0, 4.6, 5.0, 5.8, 6.6, 7.2, 8.0, 9.0]
const RANGED_WEAPONS := [&"bow", &"crossbow", &"javelin"]

static func affix_family(a: AffixDef) -> StringName:
	var s := String(a.stat)
	if s.begins_with("res_"):
		return &"resist"
	for fam in FAMILY_STATS:
		if (FAMILY_STATS[fam] as Array).has(a.stat):
			return fam
	return &"offense"

static func affix_cost(a: AffixDef) -> float:
	return float(AFFIX_COST.get(a.stat, 1.0))

static func family_limit(category: StringName, family: StringName) -> int:
	var row: Dictionary = FAMILY_LIMITS.get(category, FAMILY_LIMITS[&"_armour"])
	return int(row.get(family, 99))

## Whether `a` may join `it`'s current enchantments (ignoring the one at index `skip`, for replacements): a free group,
## room in its family, and — on weapons — relevance to what the weapon actually deals.
static func can_add(it: ItemInstance, a: AffixDef, skip := -1) -> bool:
	var fam := affix_family(a)
	var used := 0
	for i in it.affixes.size():
		if i == skip:
			continue
		var d := DB.affix(StringName(it.affixes[i].id))
		if d == null:
			continue
		if d.group == a.group:
			return false
		if affix_family(d) == fam:
			used += int(WIDE_AFFIXES.get(d.stat, 1))
	if used + int(WIDE_AFFIXES.get(a.stat, 1)) > family_limit(it.base.category, fam):
		return false
	return not it.base.is_weapon() or weapon_relevant(it, a, skip)

## A weapon's elemental increase or penetration needs that element on the weapon (its own, or a rolled added-damage
## affix); projectile damage only helps weapons that shoot or throw.
static func weapon_relevant(it: ItemInstance, a: AffixDef, skip := -1) -> bool:
	var s := String(a.stat)
	if a.stat == &"projectile_damage":
		return it.base.weapon_type in RANGED_WEAPONS
	var elem := ""
	if s.begins_with("dmg_"):
		elem = s.substr(4)
	elif s.begins_with("pen_") and a.stat != &"pen_armor" and a.stat != &"pen_elemental":
		elem = s.substr(4)
	if elem == "":
		return true
	if Elements.key(it.base.element) == StringName(elem):
		return true
	for i in it.affixes.size():
		var d := DB.affix(StringName(it.affixes[i].id))
		if i != skip and d != null and String(d.stat) == "added_" + elem:
			return true
	return false

## Strength of one rolled affix: its cost times its value relative to the best value it can ever reach.
static func affix_strength(a: Dictionary) -> float:
	var d := DB.affix(StringName(a.get("id", "")))
	if d == null or d.tiers.is_empty():
		return 0.0
	var top := absf(float(d.tiers[d.tiers.size() - 1][2]))
	return affix_cost(d) * absf(float(a.get("value", 0.0))) / maxf(top, 0.0001)

static func item_strength(it: ItemInstance) -> float:
	var t := 0.0
	for a in it.affixes:
		t += affix_strength(a)
	return t

## Pull the strongest non-masterwork rolls toward their tier minimum until the piece fits its rarity budget.
static func _fit_budget(it: ItemInstance) -> void:
	var budget: float = RARITY_BUDGET[clampi(it.rarity, 0, RARITY_BUDGET.size() - 1)]
	if budget <= 0.0:
		return
	for _pass in 12:
		var over := item_strength(it) - budget
		if over <= 0.001:
			return
		var best := -1
		var best_s := 0.0
		for i in it.affixes.size():
			var a: Dictionary = it.affixes[i]
			var d := DB.affix(StringName(a.id))
			if a.get("mw", false) or d == null:
				continue
			var floor_v := float(d.tiers[int(a.tier)][1])
			if absf(float(a.value)) - absf(floor_v) <= 0.0001:
				continue
			var s := affix_strength(a)
			if s > best_s:
				best_s = s
				best = i
		if best < 0:
			return
		var a2: Dictionary = it.affixes[best]
		var d2 := DB.affix(StringName(a2.id))
		var top := absf(float(d2.tiers[d2.tiers.size() - 1][2]))
		var want := float(a2.value) - signf(float(a2.value)) * over * top / affix_cost(d2)
		var lo := float(d2.tiers[int(a2.tier)][1])
		var v := maxf(want, lo) if float(a2.value) >= 0.0 else minf(want, lo)
		a2.value = roundf(v) if d2.integer else snappedf(v, 0.001)

## Masterwork: one enchantment is raised to the maximum value of the best tier available at this item level.
static func _perfect_one(it: ItemInstance, rng: RandomNumberGenerator) -> void:
	var i := rng.randi_range(0, it.affixes.size() - 1)
	var a: Dictionary = it.affixes[i]
	var def := DB.affix(StringName(a.id))
	if def == null:
		return
	var tiers := def.allowed_tiers(it.ilvl)
	if tiers.is_empty():
		return
	var top: int = tiers[tiers.size() - 1]
	var v := float(def.tiers[top][2])
	a["tier"] = top
	a["value"] = roundf(v) if def.integer else snappedf(v, 0.001)
	a["mw"] = true

static func _pick_license(base: ItemBaseDef, rng: RandomNumberGenerator) -> StringName:
	var ids := []
	for id in DB.licenses:
		var cats: Array = DB.licenses[id].get("categories", [])
		if (cats.is_empty() or cats.has(base.category)) and license_fits(base, DB.licenses[id]):
			ids.append(id)
	ids.sort()
	if ids.is_empty():
		return &""
	return ids[rng.randi_range(0, ids.size() - 1)]

static func _add_power(it: ItemInstance, tier: StringName, rng: RandomNumberGenerator) -> void:
	var pool := []
	for p in DB.powers_for(it.base.category):
		if p.tier == tier and not it.powers.has(String(p.id)) and power_fits(it.base, p):
			pool.append(p)
	if pool.is_empty():
		return
	# Prefer powers that suit the base's class hint (two-to-one), deterministic under the generator's RNG.
	var weighted := []
	for p in pool:
		weighted.append(p)
		if it.base.class_hint != &"" and p.class_hint == it.base.class_hint:
			weighted.append(p)
	it.powers.append(String(weighted[rng.randi_range(0, weighted.size() - 1)].id))

static func _name_for(it: ItemInstance, rng: RandomNumberGenerator) -> String:
	if it.base.unique_name != "":
		return ""
	var b := it.base
	match it.rarity:
		BH.Rarity.ELITE, BH.Rarity.MASTER:
			if b.set_id != &"":
				return ""
	# Licensed and better: ItemNames rolls a proper name and an epithet (bh-012)
	return ""

static func _weighted_pick(pool: Array, rng: RandomNumberGenerator, used: Dictionary) -> AffixDef:
	var total := 0
	for a in pool:
		if not used.has(a.group):
			total += a.weight
	if total <= 0:
		return null
	var r := rng.randi_range(1, total)
	for a in pool:
		if used.has(a.group):
			continue
		r -= a.weight
		if r <= 0:
			return a
	return null

## bh-017: the share of a hero's equipment drops (and class-hinted merchant stock) that is the hero's own class gear.
const CLASS_FIT_CHANCE := 0.80

## Armor weight each class wears: knights plate, everyone else cloth (rangers and shadowblades also keep the gambeson).
const CLASS_ARMOR := {&"knight": [&"heavy"], &"mage": [&"cloth"], &"ranger": [&"cloth"], &"shadowblade": [&"cloth"]}

## Whether `base` is gear meant for `class_id`: a weapon the class has mastery in, armor of the class's weight, a shield
## for a knight. Accessories suit everyone, so they are never "class gear".
## Class Transcendence: `class_id` may be a starting class or an advanced one (Royal Guard ...): the family decides the
## weapon / armor fit, and a piece the class may not wear (another branch's) is never its own gear. It can still drop
## as off-class loot to trade or sell.
static func class_fit(base: ItemBaseDef, class_id: StringName) -> bool:
	if class_id == &"" or base == null:
		return false
	if DataTranscendence.is_advanced(class_id):
		if not ClassRequirements.allows_class(base, class_id):
			return false
		class_id = DataTranscendence.family_of(class_id)
	elif DataTranscendence.is_family(class_id) and not ClassRequirements.allows_class(base, class_id):
		return false
	# A class set's cloth weight alone must not make mage sets ranger/shadowblade loot.
	if (base.set_id != &"" or base.unique_name != "") and base.class_hint != &"" and base.class_hint != class_id:
		return false
	var cd := DB.class_def(class_id)
	if cd == null:
		return base.class_hint == class_id
	if base.class_hint != &"" and base.class_hint != class_id:
		return false
	if base.category == &"weapon":
		return cd.weapon_mastery.has(base.weapon_type)
	if base.category == &"shield":
		return class_id == &"knight"
	if base.category in [&"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots"]:
		if (CLASS_ARMOR.get(class_id, [&"heavy"]) as Array).has(base.weight_class):
			return true
		return base.category == &"inner_garment" and base.weight_class == &"heavy" and class_id in [&"ranger", &"shadowblade"]
	return false

## bh-027: an accessory any hero of `class_id` may wear (unlabelled, or labelled for that class).
static func accessory_fits(base: ItemBaseDef, class_id: StringName) -> bool:
	if base == null or base.category != &"accessory":
		return false
	var fam := DataTranscendence.family_of(class_id) if DataTranscendence.is_identity(class_id) else class_id
	if DataTranscendence.is_identity(class_id) and not ClassRequirements.allows_class(base, class_id):
		return false
	return base.class_hint == &"" or base.class_hint == fam

## Random base eligible at an item level (weighted), optionally restricted to categories. Set pieces and uniques are
## excluded — they come from dedicated drop rolls (elites/bosses) and special merchant stock. With a `class_hint`,
## `fit_chance` of the picks come from that class's own gear (bh-017: a Knight is offered plate and blades, not robes).
static func random_base(rng: RandomNumberGenerator, ilvl: int, categories: Array = [], class_hint := &"", fit_chance := CLASS_FIT_CHANCE, excluded: Array = []) -> ItemBaseDef:
	var pool := []
	var total := 0
	for b in DB.item_bases.values():
		if not BH.CATEGORY_SLOTS.has(b.category) or b.set_id != &"" or b.unique_name != "" or b.drop_weight <= 0:
			continue
		if b.drop_level > ilvl or excluded.has(b.id):
			continue
		if not categories.is_empty() and not categories.has(b.category):
			continue
		pool.append(b)
	if pool.is_empty():
		return random_base(rng, ilvl, categories, class_hint, fit_chance) if not excluded.is_empty() else null
	# bh-027: an accessory roll (Loot asks for one alongside the weapons) skips the class-gear filter — rings suit
	# everyone — but never drops a piece labelled for another class.
	if not categories.is_empty() and categories.all(func(c): return c == &"accessory"):
		if class_hint != &"":
			pool = pool.filter(func(b): return accessory_fits(b, class_hint))
		if pool.is_empty():
			return null
	elif class_hint != &"" and rng.randf() < fit_chance:
		var mine := pool.filter(func(b): return class_fit(b, class_hint))
		if not mine.is_empty():
			pool = mine
		elif fit_chance >= 1.0:
			return random_base(rng, ilvl, categories, class_hint, fit_chance) if not excluded.is_empty() else null
	# Pick a weapon family before a base so large sword/armour catalogs cannot drown out axes.
	var weapons := pool.filter(func(b): return b.is_weapon())
	if not weapons.is_empty() and (weapons.size() == pool.size() or rng.randf() < 0.40):
		var families := []
		for b in weapons:
			if not families.has(b.weapon_type):
				families.append(b.weapon_type)
		families.sort()
		var family: StringName = families[rng.randi_range(0, families.size() - 1)]
		pool = weapons.filter(func(b): return b.weapon_type == family)
	elif weapons.size() < pool.size():
		pool = pool.filter(func(b): return not b.is_weapon())
	pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
	var weights := []
	for b in pool:
		var w: int = b.drop_weight
		# Recent bases are favoured so drops keep pace with the hero; far outleveled bases fade out.
		var age: int = maxi(0, ilvl - b.drop_level - 8)
		w = maxi(1, roundi(float(w) / (1.0 + pow(float(age) / 8.0, 2.0))))
		weights.append(w)
		total += w
	var r := rng.randi_range(1, total)
	for i in pool.size():
		r -= weights[i]
		if r <= 0:
			return pool[i]
	return pool[0]

## Dedicated roll for special items (set piece or unique) — used by elite/boss loot and rare merchant stock.
## A random consumable for a monster drop: weighted by drop_weight, level requirement at most ilvl + 3.
static func random_consumable(rng: RandomNumberGenerator, ilvl: int) -> ItemBaseDef:
	var pool := []
	var total := 0
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category != &"consumable" or b.drop_weight <= 0 or b.level_req > ilvl + 3:
			continue
		if b.id in [&"health_potion", &"mana_potion", &"greater_health_potion", &"greater_mana_potion", &"rejuvenation_elixir", &"antidote", &"return_scroll"]:
			continue   # the original potions have their own drop rolls
		pool.append(b)
		total += b.drop_weight
	if total <= 0:
		return null
	var r := rng.randi_range(1, total)
	for b in pool:
		r -= b.drop_weight
		if r <= 0:
			return b
	return pool[-1]

static func random_special(rng: RandomNumberGenerator, ilvl: int, want_set: bool, class_hint := &"", fit_chance := CLASS_FIT_CHANCE) -> ItemBaseDef:
	var pool := []
	for b in DB.item_bases.values():
		if b.drop_level > ilvl or b.boss_exclusive or b.story:
			continue
		if want_set and b.set_id != &"":
			pool.append(b)
		elif not want_set and b.unique_name != "":
			pool.append(b)
	if pool.is_empty():
		return null
	if class_hint != &"" and rng.randf() < fit_chance:
		var mine := pool.filter(func(b): return class_fit(b, class_hint) or (b.category == &"accessory" and b.class_hint == &"" and ClassRequirements.allows_class(b, class_hint)))
		if not mine.is_empty():
			pool = mine
		elif fit_chance >= 1.0:
			return null
	pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
	return pool[rng.randi_range(0, pool.size() - 1)]

## Neutral equipment supports hybrid builds. Class-labelled gear must support
## its intended class; elemental stats remain valid for converted attacks.
static func affix_fits(base: ItemBaseDef, affix: AffixDef) -> bool:
	var cls := base.class_hint
	if DataTranscendence.is_advanced(cls):
		cls = DataTranscendence.family_of(cls)
	if cls == &"":
		return true
	if cls != &"mage" and affix.stat in [&"int", &"magic_damage", &"cast_speed"]:
		return false
	if cls == &"mage" and affix.stat in [&"str", &"heavy_damage", &"impact_strength", &"pen_armor"]:
		return false
	if cls == &"knight" and affix.stat in [&"projectile_damage", &"focus_gain", &"trap_damage"]:
		return false
	if base.is_weapon() and String(affix.stat).begins_with("dmg_") and base.element != Elements.PHYSICAL:
		return affix.stat == Elements.dmg_key(base.element)
	return true

static func power_fits(base: ItemBaseDef, power: LegendaryPowerDef) -> bool:
	return base.class_hint == &"" or power.class_hint == &"" or base.class_hint == power.class_hint

## One-time repair of existing rolls. Keep roll quality, masterwork, number of
## affixes, identity and player upgrades. Deterministic; no new loot roll.
const BALANCE_VERSION := 2

static func migrate_balance(it: ItemInstance, version: int) -> void:
	if version < 1:
		_migrate_v1(it)
	if version < 2:
		_migrate_v2(it)

## bh-033: a saved piece whose enchantments break its identity (three or more resistances, All Resistances beside a
## single one, a weapon's second support roll, an elemental increase its weapon never deals) keeps the strongest of the
## clashing rolls; each other one becomes a deterministic eligible affix at the same tier index and the same percentile
## within its range. Count, masterwork, quality, sockets, upgrades and name stay. Values are not budget-trimmed: a legacy
## roll the player already owns keeps its strength.
static func _migrate_v2(it: ItemInstance) -> void:
	if it.base == null or not it.is_equipment() or it.affixes.is_empty():
		return
	# Strongest first, so the rolls that survive are the ones the player valued most.
	var order := range(it.affixes.size())
	order.sort_custom(func(x, y): return affix_strength(it.affixes[x]) > affix_strength(it.affixes[y]) or (affix_strength(it.affixes[x]) == affix_strength(it.affixes[y]) and x < y))
	var kept := []
	var bad := []
	var probe := ItemInstance.new()
	probe.base = it.base
	probe.ilvl = it.ilvl
	probe.rarity = it.rarity
	for i in order:
		var d := DB.affix(StringName(it.affixes[i].id))
		if d != null and can_add(probe, d):
			probe.affixes.append(it.affixes[i])
			kept.append(i)
		else:
			bad.append(i)
	# Relevance can depend on a later roll (dmg_fire is fine beside added_fire): one more pass with everything kept.
	for i in bad.duplicate():
		var d := DB.affix(StringName(it.affixes[i].id))
		if d != null and can_add(probe, d):
			probe.affixes.append(it.affixes[i])
			bad.erase(i)
	for i in bad:
		var a: Dictionary = it.affixes[i]
		var old := DB.affix(StringName(a.id))
		var fraction := 1.0
		if old != null:
			var ob: Array = old.tiers[clampi(int(a.tier), 0, old.tiers.size() - 1)]
			fraction = clampf(inverse_lerp(float(ob[1]), float(ob[2]), float(a.value)), 0.0, 1.0) if float(ob[2]) != float(ob[1]) else 1.0
		var pool := DB.affixes_for(it.base.category).filter(func(c): return it.rarity >= c.min_rarity and affix_fits(it.base, c) and not c.allowed_tiers(it.ilvl).is_empty() and can_add(probe, c))
		pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
		if pool.is_empty():
			continue
		var af: AffixDef = pool[posmod(hash("bh033/%s/%s/%d" % [it.base.id, a.id, it.seed_value]), pool.size())]
		var allowed := af.allowed_tiers(it.ilvl)
		var tier: int = allowed[mini(int(a.tier), allowed.size() - 1)]
		var b: Array = af.tiers[tier]
		var v := lerpf(float(b[1]), float(b[2]), 1.0 if a.get("mw", false) else fraction)
		var e := {"id": String(af.id), "tier": tier, "value": roundf(v) if af.integer else snappedf(v, 0.001)}
		if a.get("mw", false):
			e["mw"] = true
		it.affixes[i] = e
		probe.affixes.append(e)
	# Rolls with no eligible replacement are dropped rather than kept in breach of the rule.
	var cleaned := []
	for i in it.affixes.size():
		if not bad.has(i) or probe.affixes.has(it.affixes[i]):
			cleaned.append(it.affixes[i])
	it.affixes = cleaned

static func _migrate_v1(it: ItemInstance) -> void:
	if it.license != &"" and not license_fits(it.base, DB.licenses.get(it.license, {})):
		var random := RandomNumberGenerator.new()
		random.seed = it.seed_value
		it.license = _pick_license(it.base, random)
	var groups := {}
	for a in it.affixes:
		var af := DB.affix(StringName(a.id))
		if af != null and affix_fits(it.base, af):
			groups[af.group] = true
	for a in it.affixes:
		var af := DB.affix(StringName(a.id))
		if af == null:
			continue
		var tier := clampi(int(a.tier), 0, af.tiers.size() - 1)
		var old: Array = af.tiers[tier]
		if af.id == &"local_phys":
			old = [[1, 0.15, 0.30], [10, 0.30, 0.50], [20, 0.50, 0.75], [35, 0.75, 1.0]][tier]
		var fraction := clampf(inverse_lerp(float(old[1]), float(old[2]), float(a.value)), 0.0, 1.0) if float(old[2]) > float(old[1]) else 1.0
		if not affix_fits(it.base, af):
			var pool := DB.affixes_for(it.base.category).filter(func(candidate): return affix_fits(it.base, candidate) and not groups.has(candidate.group) and not candidate.allowed_tiers(it.ilvl).is_empty() and it.rarity >= candidate.min_rarity)
			pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
			if pool.is_empty():
				continue
			af = pool[posmod(hash("%s/%s/%d" % [it.base.id, a.id, it.seed_value]), pool.size())]
			var allowed := af.allowed_tiers(it.ilvl)
			tier = allowed[mini(tier, allowed.size() - 1)]
			groups[af.group] = true
		elif af.id != &"local_phys":
			continue
		var bounds: Array = af.tiers[tier]
		var value := lerpf(float(bounds[1]), float(bounds[2]), 1.0 if a.get("mw", false) else fraction)
		a.id = String(af.id)
		a.tier = tier
		a.value = roundf(value) if af.integer else snappedf(value, 0.001)
	for i in it.powers.size():
		var power := DB.power(StringName(it.powers[i]))
		if power == null or power_fits(it.base, power) or it.base.fixed_powers.has(power.id):
			continue
		var pool := DB.powers_for(it.base.category).filter(func(candidate): return candidate.tier == power.tier and power_fits(it.base, candidate) and not it.powers.has(String(candidate.id)))
		pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
		if not pool.is_empty():
			it.powers[i] = String(pool[posmod(hash("%s/%s/%d" % [it.base.id, power.id, it.seed_value]), pool.size())].id)

static func license_fits(base: ItemBaseDef, license: Dictionary) -> bool:
	for m in license.get("mods", []):
		var affix := AffixDef.new()
		affix.stat = StringName(m[0])
		if not affix_fits(base, affix):
			return false
	return true
