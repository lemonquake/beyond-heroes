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
		# bh-018: crystals keep their grade's colour tier; everything else in the bag is Common
		it.rarity = base.fixed_rarity if base.category == &"crystal" and base.fixed_rarity >= 0 else BH.Rarity.COMMON
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

## Chance of a relic power by rarity from Licensed up (Licensed, Elite, Master, Mythical, Legendary, Aether).
const RELIC_CHANCE := [0.15, 0.3, 0.45, 0.6, 0.6, 0.6]

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
static func class_fit(base: ItemBaseDef, class_id: StringName) -> bool:
	if class_id == &"" or base == null:
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
	if class_hint != &"" and rng.randf() < fit_chance:
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
		if b.drop_level > ilvl or b.boss_exclusive:
			continue
		if want_set and b.set_id != &"":
			pool.append(b)
		elif not want_set and b.unique_name != "":
			pool.append(b)
	if pool.is_empty():
		return null
	if class_hint != &"" and rng.randf() < fit_chance:
		var mine := pool.filter(func(b): return class_fit(b, class_hint) or (b.category == &"accessory" and b.class_hint == &""))
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
static func migrate_balance(it: ItemInstance, version: int) -> void:
	if version >= 1:
		return
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
