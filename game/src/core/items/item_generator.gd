class_name ItemGenerator
## Rolls rarity, affixes and legendary powers. Rarity raises affix count and tier quality — never raw multipliers
## on base stats beyond a small quality roll.

# rarity -> [min affixes, max affixes, powers, tier bias (0 = uniform over allowed, 1 = top two, 2 = top only), min value roll, max quality]
const RARITY_RULES := [
	[0, 0, 0, 0, 0.0, 0.0],     # Common
	[1, 2, 0, 0, 0.0, 0.05],    # Magic
	[3, 4, 0, 0, 0.0, 0.08],    # Rare
	[4, 5, 0, 1, 0.25, 0.12],   # Epic
	[4, 5, 1, 1, 0.4, 0.15],    # Legendary
	[5, 6, 2, 2, 0.6, 0.20],    # Mythic
]
# Base weights per rarity at 0% magic find.
const RARITY_WEIGHTS := [640.0, 250.0, 80.0, 22.0, 6.5, 1.5]

const RARE_NAME_A := ["Grim", "Ash", "Dusk", "Iron", "Blood", "Storm", "Hollow", "Rune", "Gloom", "Ember", "Raven", "Bone",
	"Frost", "Doom", "Sorrow", "Night", "Warden", "Oath", "Wraith", "Thorn"]
const RARE_NAME_B := ["Bite", "Ward", "Song", "Brand", "Veil", "Fang", "Mark", "Shroud", "Grasp", "Heart", "Coil", "Crown",
	"Edge", "Tongue", "Spire", "Wake", "Gaze", "Hold", "Vow", "Stride"]

## Rarity roll. magic_find (fraction) and bonus_tiers (elites/bosses) shift weight toward higher tiers.
static func roll_rarity(rng: RandomNumberGenerator, magic_find := 0.0, rank_bonus := 0.0) -> int:
	var w := RARITY_WEIGHTS.duplicate()
	var boost := 1.0 + maxf(0.0, magic_find) / (1.0 + maxf(0.0, magic_find) * 0.5) + rank_bonus
	for i in range(1, w.size()):
		w[i] *= pow(boost, 0.6 + 0.25 * i)
	var total := 0.0
	for x in w:
		total += x
	var r := rng.randf() * total
	for i in w.size():
		r -= w[i]
		if r <= 0.0:
			return i
	return 0

static func generate(base: ItemBaseDef, ilvl: int, rarity: int, rng: RandomNumberGenerator) -> ItemInstance:
	var it := ItemInstance.new()
	it.base = base
	it.ilvl = maxi(1, ilvl)
	it.seed_value = rng.seed
	if not BH.CATEGORY_SLOTS.has(base.category):
		it.rarity = BH.Rarity.COMMON
		return it
	it.rarity = rarity
	var rule: Array = RARITY_RULES[rarity]
	it.quality = snappedf(rng.randf_range(0.0, rule[5]), 0.01)
	var n := rng.randi_range(rule[0], rule[1])
	var pool: Array = DB.affixes_for(base.category)
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
		match int(rule[3]):
			0: tier = tiers[rng.randi_range(0, tiers.size() - 1)]
			1: tier = tiers[maxi(0, tiers.size() - 1 - rng.randi_range(0, 1))]
			_: tier = tiers[tiers.size() - 1]
		var t: Array = a.tiers[tier]
		var roll := rng.randf_range(float(rule[4]), 1.0)
		var v := lerpf(float(t[1]), float(t[2]), roll)
		v = roundf(v) if a.integer else snappedf(v, 0.001)
		it.affixes.append({"id": String(a.id), "tier": tier, "value": v})
		used_groups[a.group] = true
	var np: int = rule[2]
	if np > 0:
		var ppool := DB.powers_for(base.category)
		var salt := rng.randi()
		# deterministic shuffle keyed on the generator's RNG
		ppool.sort_custom(func(x, y): return hash(String(x.id) + str(salt)) < hash(String(y.id) + str(salt)))
		for i in mini(np, ppool.size()):
			it.powers.append(String(ppool[i].id))
	if rarity >= BH.Rarity.RARE:
		if rarity >= BH.Rarity.LEGENDARY and not it.powers.is_empty():
			var p := DB.power(StringName(it.powers[0]))
			it.custom_name = "%s %s" % [p.display_name, base.display_name] if rarity == BH.Rarity.LEGENDARY else "Mythic %s" % p.display_name
		else:
			it.custom_name = "%s %s" % [RARE_NAME_A[rng.randi_range(0, RARE_NAME_A.size() - 1)], RARE_NAME_B[rng.randi_range(0, RARE_NAME_B.size() - 1)]]
	return it

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

## Random base eligible at an item level (weighted), optionally restricted to categories.
static func random_base(rng: RandomNumberGenerator, ilvl: int, categories: Array = []) -> ItemBaseDef:
	var pool := []
	var total := 0
	for b in DB.item_bases.values():
		if not BH.CATEGORY_SLOTS.has(b.category):
			continue
		if b.drop_level > ilvl:
			continue
		if not categories.is_empty() and not categories.has(b.category):
			continue
		pool.append(b)
		total += b.drop_weight
	if pool.is_empty():
		return null
	pool.sort_custom(func(x, y): return String(x.id) < String(y.id))
	var r := rng.randi_range(1, total)
	for b in pool:
		r -= b.drop_weight
		if r <= 0:
			return b
	return pool[0]
