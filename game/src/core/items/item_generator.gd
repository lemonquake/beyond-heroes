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
]
# Relative drop weights at 0% magic find (Beginner never drops from monsters).
const WEIGHTS := [0.0, 520.0, 250.0, 130.0, 55.0, 28.0, 11.0, 4.0, 1.6, 0.25]
# Minimum item level for a tier to drop at all (keeps the first minutes of the game grounded).
const MIN_ILVL := [1, 1, 1, 1, 2, 3, 4, 5, 6, 8]

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

static func generate(base: ItemBaseDef, ilvl: int, rarity: int, rng: RandomNumberGenerator) -> ItemInstance:
	var it := ItemInstance.new()
	it.base = base
	it.ilvl = maxi(1, ilvl)
	it.seed_value = rng.seed
	if not BH.CATEGORY_SLOTS.has(base.category):
		it.rarity = BH.Rarity.COMMON
		return it
	if base.fixed_rarity >= 0:
		rarity = base.fixed_rarity
	elif base.set_id != &"":
		rarity = maxi(rarity, BH.Rarity.MASTER)
	rarity = clampi(rarity, 0, BH.RARITY_COUNT - 1)
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
	match rarity:
		BH.Rarity.MYTHICAL:
			_add_power(it, &"mythical", rng)
		BH.Rarity.LEGENDARY:
			_add_power(it, &"legendary", rng)
		BH.Rarity.AETHER:
			_add_power(it, &"legendary", rng)
			_add_power(it, &"aether", rng)
	it.custom_name = _name_for(it, rng)
	return it

static func _roll_affixes(it: ItemInstance, n: int, bias: int, min_roll: float, rng: RandomNumberGenerator) -> void:
	var pool: Array = []
	for a in DB.affixes_for(it.base.category):
		if it.rarity >= a.min_rarity:
			pool.append(a)
	var used_groups := {}
	var attempts := 0
	while it.affixes.size() < n and attempts < 64:
		attempts += 1
		var a := _weighted_pick(pool, rng, used_groups)
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
		if cats.is_empty() or cats.has(base.category):
			ids.append(id)
	ids.sort()
	if ids.is_empty():
		return &""
	return ids[rng.randi_range(0, ids.size() - 1)]

static func _add_power(it: ItemInstance, tier: StringName, rng: RandomNumberGenerator) -> void:
	var pool := []
	for p in DB.powers_for(it.base.category):
		if p.tier == tier and not it.powers.has(String(p.id)):
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
			return "%s %s" % [RARE_NAME_A[rng.randi_range(0, RARE_NAME_A.size() - 1)], RARE_NAME_B[rng.randi_range(0, RARE_NAME_B.size() - 1)]]
		BH.Rarity.MYTHICAL, BH.Rarity.LEGENDARY:
			if not it.powers.is_empty():
				var p := DB.power(StringName(it.powers[it.powers.size() - 1]))
				if p != null:
					return "%s %s" % [p.display_name, b.display_name]
		BH.Rarity.AETHER:
			for pid in it.powers:
				var p2 := DB.power(StringName(pid))
				if p2 != null and p2.tier == &"aether":
					return "%s %s" % [p2.display_name, b.display_name]
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

## Random base eligible at an item level (weighted), optionally restricted to categories. Set pieces and uniques are
## excluded — they come from dedicated drop rolls (elites/bosses) and special merchant stock.
static func random_base(rng: RandomNumberGenerator, ilvl: int, categories: Array = [], class_hint := &"") -> ItemBaseDef:
	var pool := []
	var total := 0
	for b in DB.item_bases.values():
		if not BH.CATEGORY_SLOTS.has(b.category) or b.set_id != &"" or b.unique_name != "" or b.drop_weight <= 0:
			continue
		if b.drop_level > ilvl:
			continue
		if not categories.is_empty() and not categories.has(b.category):
			continue
		pool.append(b)
	if pool.is_empty():
		return null
	pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
	var weights := []
	for b in pool:
		var w: int = b.drop_weight
		# Recent bases are favoured so drops keep pace with the hero; far outleveled bases fade out.
		if ilvl - b.drop_level > 12:
			w = maxi(1, w / 4)
		if class_hint != &"" and b.class_hint == class_hint:
			w *= 2
		weights.append(w)
		total += w
	var r := rng.randi_range(1, total)
	for i in pool.size():
		r -= weights[i]
		if r <= 0:
			return pool[i]
	return pool[0]

## Dedicated roll for special items (set piece or unique) — used by elite/boss loot and rare merchant stock.
static func random_special(rng: RandomNumberGenerator, ilvl: int, want_set: bool) -> ItemBaseDef:
	var pool := []
	for b in DB.item_bases.values():
		if b.drop_level > ilvl:
			continue
		if want_set and b.set_id != &"":
			pool.append(b)
		elif not want_set and b.unique_name != "":
			pool.append(b)
	if pool.is_empty():
		return null
	pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
	return pool[rng.randi_range(0, pool.size() - 1)]
