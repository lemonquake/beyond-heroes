class_name LapeTrade
extends RefCounted
## bh-019, reworked in bh-041: Lape the Ancient's special trade (Malasugue). The hero lays up to three items from the
## bag in his brass dishes; Lape appraises them (value + his remarks, DataLapeLines), identifies what is in them, reads
## what the lot has in common, and draws his offers. Taking one ends the trade: the items go to Lape.
##
## Rules
##   gold      = sum of base_value x count x GOLD_RATE (merchants pay 25 % of base value, Lape 45 %)
##   craft     = only when the lot is worth at least craft_floor(level) gold; otherwise he offers only the gold
##   tier      = the best tier laid down (Licensed at the least); +1 when all three dishes hold that tier or one below;
##               never above Legendary unless an Aether (or higher) piece was laid down; crafted pieces stop at Aether
##   essence   = what the lot has in common (essence()): its kinds of gear, its elements (bases and crystals), the
##               sets it comes from, Ascendant and Fabled pieces, filled sockets. It steers every offer:
##   offers    = three to five, by the lot's worth, drawn from these kinds (OFFER_KIND):
##                 crafted    a licensed piece for the hero's class; kinds of gear laid down come up more often, and
##                            now and then one comes out a tier higher (or lower) than the rest
##                 reforged   one of the laid pieces itself, made again one tier higher (plain bases, Elite..Legendary)
##                 mended     a missing piece of a collection laid down (Ascendant and Eschaton sets)
##                 fabled     another Fabled arm of the tier, when one was laid down
##                 ascendant  an Ascendant piece when Ascendant work was laid down, up to its tier
##                 hoard      a stack of crystals of the lot's element, when it carries crystals or leans one way
##                 eschaton   (the last work, DataEschaton) with eschaton_chance(): the higher the Ascendant tiers laid
##                            down, the likelier; three Primordial pieces make it more likely than not
##               there is always a weapon among them, and the gold
##   draw      = the offers come from the lot itself (the same lot always draws the same offers); paying him to look
##               again (redraw_cost) draws a new set from the same lot, as often as the hero can pay

const MAX_ITEMS := 3
const GOLD_RATE := 0.45
## Upper bounds (gold) of the worth bands the remarks use: scraps, modest, fair, good, great, treasure.
const VALUE_BANDS := [15, 80, 400, 2000, 10000]
const ARMOR_CATS := [&"helm", &"armor", &"leggings", &"gloves", &"boots", &"inner_garment", &"shield"]
const MAX_OFFERS := 5
## How much each tier laid down weighs towards the last work (eschaton_chance).
const ESCHATON_WEIGHT := {BH.Rarity.LEGENDARY: 0.05, BH.Rarity.AETHER: 0.25, BH.Rarity.COSMIC: 1.0, BH.Rarity.DIVINE: 2.0,
	BH.Rarity.ETERNAL: 4.0, BH.Rarity.PRIMORDIAL: 8.0, BH.Rarity.ESCHATON: 10.0}
const ESCHATON_SCALE := 24.0
const ESCHATON_CAP := 0.75
## The crystal family a lot's element asks for (the hoard offer).
const ELEMENT_CRYSTAL := {Elements.FIRE: &"ember", Elements.WATER: &"aqua", Elements.ICE: &"aqua", Elements.LIGHT: &"nova",
	Elements.LIGHTNING: &"thundra", Elements.DARK: &"luna", Elements.WIND: &"airah", Elements.EARTH: &"vipera", Elements.PHYSICAL: &"aetherift"}
const CRYSTAL_ELEMENT := {&"ember": Elements.FIRE, &"aqua": Elements.WATER, &"nova": Elements.LIGHT, &"thundra": Elements.LIGHTNING,
	&"luna": Elements.DARK, &"airah": Elements.WIND, &"vipera": Elements.EARTH, &"sol": Elements.LIGHT, &"sora": Elements.WIND}

## Why Lape will not take an item ("" when he will).
static func refuse_reason(it: ItemInstance) -> String:
	if it == null:
		return "Nothing there."
	if it.is_protected():
		return "Locked and favourite items stay with you. Unlock it first."
	if not it.base.sellable or it.base.is_quest():
		return "Lape will not take that."
	return ""

## Gold Lape pays for one item (the whole stack).
static func item_value(it: ItemInstance) -> int:
	return maxi(1, int(round(it.base_value() * GOLD_RATE))) * maxi(1, it.count)

static func craft_floor(level: int) -> int:
	return 60 + 18 * maxi(1, level)

## The tier Lape crafts for this lot (BH.Rarity).
static func craft_tier(items: Array) -> int:
	var best := BH.Rarity.COMMON
	for it: ItemInstance in items:
		best = maxi(best, it.rarity)
	var tier := maxi(BH.Rarity.LICENSED, best)
	if items.size() >= MAX_ITEMS:
		var all_close := true
		for it: ItemInstance in items:
			if it.rarity < best - 1:
				all_close = false
		if all_close:
			tier += 1
	var cap := BH.Rarity.AETHER if best >= BH.Rarity.AETHER else BH.Rarity.LEGENDARY
	return clampi(tier, BH.Rarity.LICENSED, cap)

static func _key(it: ItemInstance) -> String:
	return "%s/%d/%d/%d/%d" % [it.base.id, it.seed_value, it.rarity, it.ilvl, it.count]

static func lot_seed(items: Array, hero: HeroData) -> int:
	var keys := PackedStringArray()
	for it: ItemInstance in items:
		keys.append("%s/%d/%d/%d/%d" % [it.base.id, it.seed_value, it.rarity, it.ilvl, it.count])
	keys.sort()
	return hash("lape|%s|%s" % [hero.hero_name if hero else "", "|".join(keys)])

## Chance that the last work is among the offers (per draw), from the tiers laid down: 1 - e^(-score / 24), at most 75 %.
## Three Primordial pieces: 63 %; one: 28 %; three Eternal: 39 %; three Cosmic: 12 %; three Aether: 3 %.
static func eschaton_chance(items: Array) -> float:
	var score := 0.0
	for it: ItemInstance in items:
		if it.is_equipment():
			score += float(ESCHATON_WEIGHT.get(it.rarity, 0.0))
	return minf(ESCHATON_CAP, 1.0 - exp(-score / ESCHATON_SCALE)) if score > 0.0 else 0.0

## What a lot has in common: {cats {category: n}, elements {element: weight}, sets {set id: n}, best, ascendant [items],
## fabled [items], gems n, level (best item level)}.
static func essence(items: Array) -> Dictionary:
	var out := {"cats": {}, "elements": {}, "sets": {}, "best": BH.Rarity.COMMON, "ascendant": [], "fabled": [], "gems": 0, "level": 1}
	for it: ItemInstance in items:
		var c: StringName = it.base.category
		out.cats[c] = int(out.cats.get(c, 0)) + 1
		out.best = maxi(out.best, it.rarity)
		out.level = maxi(out.level, it.ilvl)
		if it.base.element_share > 0.0 and it.base.element != Elements.PHYSICAL:
			out.elements[it.base.element] = float(out.elements.get(it.base.element, 0.0)) + 1.0 + it.base.element_share
		for g in it.gems:
			var fam := DataCrystals.family_of(StringName(g))
			if fam != &"":
				out.gems += 1
				if CRYSTAL_ELEMENT.has(fam):
					out.elements[CRYSTAL_ELEMENT[fam]] = float(out.elements.get(CRYSTAL_ELEMENT[fam], 0.0)) + 0.6
		if DataCrystals.is_crystal(it.base.id):
			var fam2 := DataCrystals.family_of(it.base.id)
			if CRYSTAL_ELEMENT.has(fam2):
				out.elements[CRYSTAL_ELEMENT[fam2]] = float(out.elements.get(CRYSTAL_ELEMENT[fam2], 0.0)) + float(it.count)
		if it.base.set_id != &"":
			out.sets[it.base.set_id] = int(out.sets.get(it.base.set_id, 0)) + 1
		if DataAscendant.is_ascendant(it.base):
			out.ascendant.append(it)
		if DataFabled.is_fabled(it.base):
			out.fabled.append(it)
	return out

## The lot's leading element (-1 when it has none).
static func lead_element(ess: Dictionary) -> int:
	var best := -1
	var bw := 0.0
	for e in ess.elements:
		if float(ess.elements[e]) > bw:
			bw = float(ess.elements[e])
			best = int(e)
	return best

## What the lot has in common, for his remarks: keys of DataLapeLines.COMBO.
static func combos(items: Array, ess: Dictionary) -> Array:
	var out := []
	if eschaton_chance(items) >= 0.25:
		out.append(&"omen")
	if items.size() >= 2 and (ess.cats as Dictionary).size() == 1:
		out.append(&"same_kind")
	for s in ess.sets:
		if int(ess.sets[s]) >= 2:
			out.append(&"same_set")
			break
	if lead_element(ess) >= 0 and float(ess.elements[lead_element(ess)]) >= 2.0:
		out.append(&"element")
	if not (ess.ascendant as Array).is_empty():
		out.append(&"ascendant")
	if not (ess.fabled as Array).is_empty():
		out.append(&"fabled")
	if int(ess.gems) >= 3:
		out.append(&"socketed")
	if out.is_empty() and items.size() >= 2:
		out.append(&"mixed")
	return out

## Gold Lape asks to draw again from the same lot, for the `n`th time (1 = the first redraw): it grows each time.
static func redraw_cost(appraisal: Dictionary, n: int) -> int:
	return maxi(50, int(round(float(appraisal.get("value", 0)) * 0.06 * float(n))))

## The full appraisal of a lot: {value, craft, tier, items: [{item, value, lines, facts}], summary, offers, kinds,
## draw, chance (of the last work), eschaton (it is among the offers), combos}. `draw` 0 is his first look.
static func appraise(hero: HeroData, items: Array, draw := 0) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = lot_seed(items, hero) + draw * 7919
	var out := {"value": 0, "craft": false, "tier": BH.Rarity.LICENSED, "items": [], "summary": PackedStringArray(), "offers": [],
		"kinds": [], "draw": draw, "chance": eschaton_chance(items), "eschaton": false, "combos": []}
	var who := hero.hero_name if hero else "hero"
	var total := 0
	var max_ilvl := 1
	for it: ItemInstance in items:
		var v := item_value(it)
		total += v
		max_ilvl = maxi(max_ilvl, it.ilvl)
		out.items.append({"item": it, "value": v, "lines": remarks(it, v, who), "facts": facts(it)})
	out.value = total
	var level := hero.progress.level if hero else 1
	out.craft = not items.is_empty() and total >= craft_floor(level)
	if not out.craft:
		out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.DECLINE, rng), null, who))
		return out
	out.tier = craft_tier(items)
	# the dishes' order changes nothing: the lot is read in a fixed order
	var lot := items.duplicate()
	lot.sort_custom(func(a: ItemInstance, b: ItemInstance) -> bool: return _key(a) < _key(b))
	var ess := essence(lot)
	out.combos = combos(lot, ess)
	var ilvl := clampi(max_ilvl, level, level + 2)
	var drawn := draw_offers(hero, lot, ess, out.tier, ilvl, total, rng)
	out.offers = drawn.offers
	out.kinds = drawn.kinds
	out.eschaton = (drawn.kinds as Array).has(&"eschaton")
	if draw > 0:
		out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.REDRAW, rng), null, who))
	for c in out.combos:
		out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.COMBO[c], rng), null, who))
	var top := int(out.tier)
	for it: ItemInstance in out.offers:
		top = maxi(top, it.rarity)
	out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.OFFER[clampi(top - BH.Rarity.LICENSED, 0, DataLapeLines.OFFER.size() - 1)], rng), null, who))
	if out.eschaton:
		out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.ESCHATON_REVEAL, rng), null, who))
	out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.REQS, rng), null, who))
	return out

## The draw: {offers: [ItemInstance], kinds: [StringName]} (see the rules above). Crafted pieces first, the special
## offers after them, the last work (if it comes) last.
static func draw_offers(hero: HeroData, items: Array, ess: Dictionary, tier: int, ilvl: int, value: int, rng: RandomNumberGenerator) -> Dictionary:
	var cid: StringName = ClassTranscendence.current_class_id(hero) if hero and hero.cls else &""
	var fam: StringName = hero.cls.id if hero and hero.cls else &""
	var level := hero.progress.level if hero else ilvl
	var floor_ := craft_floor(level)
	var n := 3 + (1 if value >= floor_ * 6 else 0) + (1 if value >= floor_ * 40 else 0)
	n = mini(n, MAX_OFFERS)
	var special := []           # [kind, item]
	var used := {}
	for it: ItemInstance in items:
		used[it.base.id] = true
	# the last work
	var chance := eschaton_chance(items)
	if chance > 0.0 and rng.randf() < chance:
		special.append([&"eschaton", DataEschaton.roll(fam, rng, maxi(level, DataEschaton.ITEM_LEVEL), ess.cats)])
		if chance >= 0.5 and rng.randf() < chance * 0.2:
			special.append([&"eschaton", DataEschaton.roll(fam, rng, maxi(level, DataEschaton.ITEM_LEVEL), ess.cats)])
	# a missing piece of a collection laid down
	var mended := _mend(hero, items, ess, rng)
	if mended and rng.randf() < 0.65:
		special.append([&"mended", mended])
	# Ascendant work for Ascendant work
	if int(ess.best) >= BH.Rarity.COSMIC and rng.randf() < 0.5:
		var top := mini(int(ess.best), BH.Rarity.PRIMORDIAL)
		var r := top if rng.randf() < 0.55 else rng.randi_range(BH.Rarity.COSMIC, top)
		var asc := DataAscendant.roll_drop(maxi(level, int(DataAscendant.TIER[r].item_level)), false, fam, 0.0, rng, r)
		if asc:
			special.append([&"ascendant", asc])
	# a Fabled arm retold
	if not (ess.fabled as Array).is_empty() and rng.randf() < 0.55:
		var fr: int = (ess.fabled[0] as ItemInstance).rarity
		var arms := DataFabled.ids_of(fr).filter(func(id): return not used.has(id) and (fam == &"" or ItemGenerator.class_fit(DB.item_base(id), fam)))
		if not arms.is_empty():
			special.append([&"fabled", DB.make_item(arms[rng.randi_range(0, arms.size() - 1)], fr, maxi(ilvl, (ess.fabled[0] as ItemInstance).ilvl), rng.randi())])
	# one of the laid pieces, made again a tier higher
	var reforge := []
	for it: ItemInstance in items:
		if it.is_equipment() and it.rarity >= BH.Rarity.ELITE and it.rarity < BH.Rarity.AETHER and it.base.fixed_rarity < 0 \
				and it.base.unique_name == "" and it.base.set_id == &"":
			reforge.append(it)
	if not reforge.is_empty() and rng.randf() < 0.45:
		var src: ItemInstance = reforge[rng.randi_range(0, reforge.size() - 1)]
		var re := ItemGenerator.generate(src.base, maxi(ilvl, src.ilvl), src.rarity + 1, rng)
		re.crafted = true
		re.sockets = maxi(re.sockets, src.sockets)
		while re.gems.size() < re.sockets:
			re.gems.append("")
		special.append([&"reforged", re])
	# a hoard of crystals of the lot's element
	var el := lead_element(ess)
	if (int(ess.gems) >= 2 or el >= 0) and rng.randf() < 0.35:
		var cfam: StringName = ELEMENT_CRYSTAL.get(el, DataCrystals.COMMON[rng.randi_range(0, DataCrystals.COMMON.size() - 1)])
		var grade := clampi(int(tier - BH.Rarity.ELITE) / 2 + (1 if level >= 60 else 0), 0, 3)
		var cid2 := DataCrystals.id_of(cfam, grade)
		if DB.item_base(cid2):
			var hoard := DB.make_item(cid2, BH.Rarity.COMMON, 1, rng.randi())
			hoard.count = clampi(2 + rng.randi_range(0, 2), 1, maxi(1, hoard.base.stack_max))
			special.append([&"hoard", hoard])
	# keep the specials within the table (the last work always stays)
	while special.size() > n - 1:
		var drop := -1
		for i in range(special.size() - 1, -1, -1):
			if special[i][0] != &"eschaton":
				drop = i
				break
		if drop < 0:
			break
		special.remove_at(drop)
	# crafted pieces fill the rest, leaning to the kinds of gear laid down
	var crafted := []
	for i in maxi(0, n - special.size()):
		var c := _crafted(hero, cid, _pick_cats(ess, rng, i), _vary_tier(tier, rng), ilvl, rng, used)
		if c:
			crafted.append(c)
	var offers := []
	var kinds := []
	for c in crafted:
		offers.append(c)
		kinds.append(&"crafted")
	special.sort_custom(func(a, b): return int(a[0] == &"eschaton") < int(b[0] == &"eschaton"))
	for s in special:
		offers.append(s[1])
		kinds.append(s[0])
	# there is always a weapon on the table
	var has_weapon := false
	for it: ItemInstance in offers:
		if it.base.category == &"weapon":
			has_weapon = true
	if not has_weapon:
		var w := _crafted(hero, cid, [&"weapon"], tier, ilvl, rng, used)
		if w:
			var at := kinds.find(&"crafted")
			if at >= 0:
				offers[at] = w
			else:
				offers.push_front(w)
				kinds.push_front(&"crafted")
	return {"offers": offers, "kinds": kinds}

## Kinds of gear for crafted offer `i`: what was laid down weighs three times as much; the first one is a weapon when
## nothing in particular was laid down.
static func _pick_cats(ess: Dictionary, rng: RandomNumberGenerator, i: int) -> Array:
	var groups := [[&"weapon"], ARMOR_CATS, [&"accessory"]]
	var weights := [1.2, 1.4, 0.7]
	for c in ess.cats:
		if c == &"weapon":
			weights[0] += 3.0 * float(ess.cats[c])
		elif ARMOR_CATS.has(c):
			weights[1] += 3.0 * float(ess.cats[c])
		elif c == &"accessory":
			weights[2] += 3.0 * float(ess.cats[c])
	if i == 0 and (ess.cats as Dictionary).is_empty():
		return [&"weapon"]
	var g: Array = groups[DataAscendant._weighted(weights, rng)]
	# armour: lean to the very slots laid down
	if g == ARMOR_CATS:
		var laid := ARMOR_CATS.filter(func(c): return ess.cats.has(c))
		if not laid.is_empty() and rng.randf() < 0.6:
			return [laid[rng.randi_range(0, laid.size() - 1)]]
	return g

## Most offers come out at the lot's tier; now and then one a tier lower, or (Lape's whim) a tier higher.
static func _vary_tier(tier: int, rng: RandomNumberGenerator) -> int:
	var cap := BH.Rarity.AETHER if tier >= BH.Rarity.LEGENDARY else BH.Rarity.LEGENDARY
	var r := rng.randf()
	if r < 0.12:
		return clampi(tier + 1, BH.Rarity.LICENSED, cap)
	if r < 0.3:
		return clampi(tier - 1, BH.Rarity.LICENSED, cap)
	return tier

## A licensed piece for the hero's class from one of `cats` (any armour when none fits), at `tier`.
static func _crafted(hero: HeroData, cid: StringName, cats: Array, tier: int, ilvl: int, rng: RandomNumberGenerator, used: Dictionary) -> ItemInstance:
	for attempt in 14:
		var pool: Array = cats if attempt < 9 else ARMOR_CATS
		var b := ItemGenerator.random_base(rng, ilvl, pool, cid, 1.0)
		if b == null or used.has(b.id):
			continue
		var cand := ItemGenerator.generate(b, ilvl, tier, rng)
		if cand.license == &"":
			cand.license = ItemGenerator._pick_license(b, rng)
		if cand.license == &"":
			continue
		cand.crafted = true
		used[b.id] = true
		return cand
	return null

## A piece of an Ascendant or Eschaton collection laid down that the lot does not hold and the hero does not wear
## (null when there is none to give).
static func _mend(hero: HeroData, items: Array, ess: Dictionary, rng: RandomNumberGenerator) -> ItemInstance:
	var held := {}
	for it: ItemInstance in items:
		held[it.base.id] = true
	if hero:
		for slot in hero.equipment.slots:
			var w: ItemInstance = hero.equipment.slots[slot]
			if w:
				held[w.base.id] = true
	var fam: StringName = hero.cls.id if hero and hero.cls else &""
	for it: ItemInstance in ess.ascendant:
		var sid := it.base.set_id
		if sid == &"":
			continue
		var sd := DB.item_set(sid)
		if sd == null:
			continue
		var missing := []
		for pid in sd.pieces:
			var b := DB.item_base(pid)
			if b and not held.has(pid) and (b.category != &"shield" or fam == &"knight") and (b.category != &"weapon" or fam == &"" or ItemGenerator.class_fit(b, fam)):
				missing.append(pid)
		if not missing.is_empty():
			var pid: StringName = missing[rng.randi_range(0, missing.size() - 1)]
			return DB.make_item(pid, it.rarity, maxi(it.ilvl, hero.progress.level if hero else it.ilvl), rng.randi())
	return null

## Three crafted offers: a weapon, an armour piece and a piece of jewellery (the bh-019 trio; the cheat and probes use it).
static func make_offers(hero: HeroData, tier: int, ilvl: int, rng: RandomNumberGenerator) -> Array:
	var cid: StringName = ClassTranscendence.current_class_id(hero) if hero and hero.cls else &""
	var out := []
	var used := {}
	for cats in [[&"weapon"], ARMOR_CATS, [&"accessory"]]:
		var it := _crafted(hero, cid, cats, tier, ilvl, rng, used)
		if it:
			out.append(it)
	return out

## His remarks on one item: an opening look, its kind, its tier, what identifying it turned up, and its worth.
static func remarks(it: ItemInstance, value: int, who: String) -> PackedStringArray:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("lape-item|%s|%d|%d|%d" % [it.base.id, it.seed_value, it.rarity, it.count])
	var L := DataLapeLines
	var out := PackedStringArray()
	out.append(L.fill(L.pick(L.OPEN, rng), it, who))
	var kind: StringName = it.base.category if L.KIND.has(it.base.category) else &"other"
	out.append(L.fill(L.pick(L.KIND[kind], rng), it, who))
	if it.is_equipment():
		out.append(L.fill(L.pick(L.TIER[clampi(it.rarity, 0, BH.RARITY_COUNT - 1)], rng), it, who))
	# identification: the two most telling things about it
	var found := _findings(it)
	for i in mini(2, found.size()):
		var f: Array = found[i]
		out.append(L.fill(L.pick(L.FIND[f[0]], rng), it, who, int(f[1])))
	var band := VALUE_BANDS.size()
	for i in VALUE_BANDS.size():
		if value <= int(VALUE_BANDS[i]):
			band = i
			break
	out.append(L.fill(L.pick(L.WORTH[band], rng), it, who))
	return out

## What identifying the item turns up, most telling first: [finding key, number].
static func _findings(it: ItemInstance) -> Array:
	var out := []
	var gems := 0
	for g in it.gems:
		if String(g) != "":
			gems += 1
	if it.base.unique_name != "":
		out.append([&"unique", 0])
	if it.base.set_id != &"":
		out.append([&"set", 0])
	if not it.powers.is_empty():
		out.append([&"powers", it.powers.size()])
	if gems > 0:
		out.append([&"sockets_filled", gems])
	elif it.sockets > 0:
		out.append([&"sockets_empty", it.sockets])
	if it.enchant != &"" and it.enchant_rank > 0:
		out.append([&"enchant", it.enchant_rank])
	if it.foretech != &"" and it.foretech_rank > 0:
		out.append([&"foretech", it.foretech_rank])
	if it.license != &"":
		out.append([&"license", 0])
	if it.is_equipment():
		if it.affixes.size() >= 4:
			out.append([&"many_affixes", it.affixes.size()])
		if it.quality >= 0.12:
			out.append([&"quality_high", 0])
		if it.custom_name != "" and it.base.unique_name == "":
			out.append([&"named", 0])
		if it.ilvl >= 25:
			out.append([&"ilvl_high", it.ilvl])
		elif it.ilvl <= 4 and it.rarity <= BH.Rarity.BASIC:
			out.append([&"ilvl_low", it.ilvl])
		if it.affixes.is_empty():
			out.append([&"no_affixes", 0])
		elif it.quality <= 0.01:
			out.append([&"quality_low", 0])
		if it.weight() >= 12.0:
			out.append([&"heavy", 0])
		elif it.weight() <= 1.0:
			out.append([&"light", 0])
	if it.count > 1:
		out.append([&"stack", it.count])
	return out

## The plain facts he identifies (shown under his remarks).
static func facts(it: ItemInstance) -> PackedStringArray:
	var out := PackedStringArray()
	if it.is_equipment():
		out.append("%s %s · item level %d · quality +%d%%" % [it.rarity_name(), it.base.display_name, it.ilvl, roundi(it.quality * 100.0)])
		var bits := PackedStringArray()
		bits.append("%d enchantment%s" % [it.affixes.size(), "" if it.affixes.size() == 1 else "s"])
		if not it.powers.is_empty():
			bits.append("%d power%s" % [it.powers.size(), "" if it.powers.size() == 1 else "s"])
		if it.sockets > 0:
			var gems := 0
			for g in it.gems:
				if String(g) != "":
					gems += 1
			bits.append("%d socket%s (%d set)" % [it.sockets, "" if it.sockets == 1 else "s", gems])
		if it.license != &"":
			bits.append("%s license" % String(DB.licenses.get(it.license, {}).get("name", "")))
		if it.enchant_rank > 0:
			bits.append("rune rank %d" % it.enchant_rank)
		if it.foretech_rank > 0:
			bits.append("Fore-Tech +%d" % it.foretech_rank)
		out.append(" · ".join(bits))
	else:
		out.append("%s%s" % [it.base.display_name, " x%d" % it.count if it.count > 1 else ""])
	return out

## What a hero must know before choosing a piece: [text, ok] lines (ok false = not met yet, null = information).
static func requirements(hero: HeroData, it: ItemInstance) -> Array:
	var out := []
	var lic: Dictionary = DB.licenses.get(it.license, {})
	if not lic.is_empty():
		var mods := PackedStringArray()
		for m: StatModifier in it.license_modifiers():
			mods.append(StatDefs.format_modifier(m.stat, m.op, m.value))
		out.append(["Licensed: %s. %s License bonus: %s." % [lic.get("name", ""), lic.get("desc", ""), ", ".join(mods)], null])
	if not it.is_equipment():
		out.append(["%d x %s, ready to set in a socket." % [it.count, it.display_name()], null])
		return out
	if hero == null:
		out.append([ClassRequirements.text(it.base), null])
		return out
	for line in ClassRequirements.lines(it.base, hero):
		out.append(line)
	if not it.base.wearers.is_empty():
		out.append([DataSpecialWeapons.wearers_text(it.base) + ".", hero.cls == null or DataSpecialWeapons.can_wear(it.base, hero.cls.id)])
	if it.unbound:
		out.append(["Unbound: no level or attribute requirement; wearable from Class %s." % DataGuilds.letter(DataSpecialWeapons.UNBOUND_RANK),
			hero.tier >= DataSpecialWeapons.UNBOUND_RANK])
		return out
	var lvl := hero.progress.level
	out.append(["Requires level %d" % it.required_level(), lvl >= it.required_level()])
	var need := DataGuilds.rank_for_rarity(it.rarity)
	if need > 0:
		out.append(["Requires a Class %s hero (%s gear) — you are %s" % [DataGuilds.letter(need), it.rarity_name(), DataGuilds.tier_name(hero.tier)],
			hero.equipment.tier_rank >= need])
	var attrs := hero.progress.base_attributes()
	for a in it.base.requirements:
		out.append(["Requires %d %s (you have %d)" % [it.base.requirements[a], BH.ATTRIBUTE_NAMES[a], int(attrs.get(a, 0))],
			int(attrs.get(a, 0)) >= int(it.base.requirements[a])])
	var cid: StringName = ClassTranscendence.current_class_id(hero) if hero.cls else &""
	if it.base.category != &"accessory":
		out.append(["Made for your class" if ItemGenerator.class_fit(it.base, cid) else "Not your class's usual gear", ItemGenerator.class_fit(it.base, cid)])
	var err := hero.equipment.check(it, hero.equipment.auto_slot(it), lvl, attrs)
	out.append(["You can wear it now" if err == "" else "Not yet wearable: %s" % err, err == ""])
	return out

## Pay Lape to look again at the same lot. Returns {ok, error, appraisal, cost}: the new appraisal is draw n + 1.
static func redraw(hero: HeroData, items: Array, appraisal: Dictionary) -> Dictionary:
	var n := int(appraisal.get("draw", 0)) + 1
	var cost := redraw_cost(appraisal, n)
	if hero == null or items.is_empty() or not appraisal.get("craft", false):
		return {"ok": false, "error": "Lape has nothing to look at again.", "appraisal": appraisal, "cost": cost}
	if hero.inventory.gold < cost:
		return {"ok": false, "error": "Lape asks %d gold to look again; you have %d." % [cost, hero.inventory.gold], "appraisal": appraisal, "cost": cost}
	for it: ItemInstance in items:
		if hero.inventory.index_of(it) < 0:
			return {"ok": false, "error": "%s is no longer in your bag." % it.display_name(), "appraisal": appraisal, "cost": cost}
	hero.inventory.gold -= cost
	hero.inventory.changed.emit()
	return {"ok": true, "error": "", "appraisal": appraise(hero, items, n), "cost": cost}

## Close the trade. choice = index of the offer to take, or -1 for the gold. Returns {ok, error, item, gold, line, kind}.
static func accept(hero: HeroData, items: Array, appraisal: Dictionary, choice: int) -> Dictionary:
	var res := {"ok": false, "error": "", "item": null, "gold": 0, "line": "", "kind": &""}
	if hero == null or items.is_empty():
		res.error = "Nothing to trade."
		return res
	for it: ItemInstance in items:
		if hero.inventory.index_of(it) < 0:
			res.error = "%s is no longer in your bag." % it.display_name()
			return res
		var why := refuse_reason(it)
		if why != "":
			res.error = why
			return res
	var offers: Array = appraisal.get("offers", [])
	if choice >= 0 and (not appraisal.get("craft", false) or choice >= offers.size()):
		res.error = "Lape has not offered that."
		return res
	for it: ItemInstance in items:
		hero.inventory.remove_item(it)
	var rng := RandomNumberGenerator.new()
	rng.seed = lot_seed(items, hero) + 7
	var who := hero.hero_name
	if choice < 0:
		res.gold = int(appraisal.get("value", 0))
		hero.inventory.gold += res.gold
		res.line = DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.AFTER_GOLD, rng), null, who)
	else:
		var got: ItemInstance = offers[choice]
		var kinds: Array = appraisal.get("kinds", [])
		res.kind = kinds[choice] if choice < kinds.size() else &"crafted"
		if hero.inventory.add(got) > 0 or (got.count <= 1 and hero.inventory.index_of(got) < 0 and not got.base.is_stackable()):
			# no room (cannot happen: the traded items just freed their cells) — undo
			for it: ItemInstance in items:
				hero.inventory.add(it)
			res.error = "Your bag is full."
			return res
		res.item = got
		var pool: Array = DataLapeLines.AFTER_ESCHATON if res.kind == &"eschaton" else DataLapeLines.AFTER_ITEM
		res.line = DataLapeLines.fill(DataLapeLines.pick(pool, rng), got, who)
	hero.inventory.changed.emit()
	res.ok = true
	return res
