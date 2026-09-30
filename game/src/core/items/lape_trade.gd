class_name LapeTrade
extends RefCounted
## bh-019: Lape the Ancient's special trade (Malasugue). The hero lays up to three items from the bag in his brass
## dishes; Lape appraises them (value + his remarks, DataLapeLines), identifies what is in them, and offers three
## special-crafted pieces of equipment, every one of them carrying a faction license, made for the hero's class, or
## the gold instead. Taking one ends the trade: the items go to Lape.
##
## Rules
##   gold      = sum of base_value x count x GOLD_RATE (merchants pay 25 % of base value, Lape 45 %)
##   craft     = only when the lot is worth at least craft_floor(level) gold; otherwise he offers only the gold
##   tier      = the best tier laid down (Licensed at the least); +1 when all three dishes hold that tier or one below;
##               never above Legendary unless an Aether piece was laid down
##   offers    = one weapon, one armour piece and one piece of jewellery (or armour when no ring fits), at the hero's
##               level (or the best item level laid down, at most the hero's level + 2), each with a license
##   seed      = from the laid-down items themselves, so the same lot always draws the same offers and remarks
##               (taking the items out and in again does not re-roll)

const MAX_ITEMS := 3
const GOLD_RATE := 0.45
## Upper bounds (gold) of the worth bands the remarks use: scraps, modest, fair, good, great, treasure.
const VALUE_BANDS := [15, 80, 400, 2000, 10000]
const ARMOR_CATS := [&"helm", &"armor", &"leggings", &"gloves", &"boots", &"inner_garment", &"shield"]

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

static func lot_seed(items: Array, hero: HeroData) -> int:
	var keys := PackedStringArray()
	for it: ItemInstance in items:
		keys.append("%s/%d/%d/%d/%d" % [it.base.id, it.seed_value, it.rarity, it.ilvl, it.count])
	keys.sort()
	return hash("lape|%s|%s" % [hero.hero_name if hero else "", "|".join(keys)])

## The full appraisal of a lot: {value, craft, tier, items: [{item, value, lines, facts}], summary, offers}.
static func appraise(hero: HeroData, items: Array) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = lot_seed(items, hero)
	var out := {"value": 0, "craft": false, "tier": BH.Rarity.LICENSED, "items": [], "summary": PackedStringArray(), "offers": []}
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
	var ilvl := clampi(max_ilvl, level, level + 2)
	out.offers = make_offers(hero, out.tier, ilvl, rng)
	out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.OFFER[clampi(out.tier - BH.Rarity.LICENSED, 0, 5)], rng), null, who))
	out.summary.append(DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.REQS, rng), null, who))
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

## Three crafted offers: a weapon, an armour piece and a piece of jewellery, all fitted to the hero's class and
## every one with a faction license.
static func make_offers(hero: HeroData, tier: int, ilvl: int, rng: RandomNumberGenerator) -> Array:
	var cid: StringName = hero.cls.id if hero and hero.cls else &""
	var out := []
	var used := {}
	for cats in [[&"weapon"], ARMOR_CATS, [&"accessory"]]:
		var it: ItemInstance = null
		for attempt in 12:
			var pool: Array = cats if attempt < 8 else ARMOR_CATS
			var b := ItemGenerator.random_base(rng, ilvl, pool, cid, 1.0)
			if b == null or used.has(b.id):
				continue
			var cand := ItemGenerator.generate(b, ilvl, tier, rng)
			if cand.license == &"":
				cand.license = ItemGenerator._pick_license(b, rng)
			if cand.license == &"":
				continue
			it = cand
			break
		if it:
			it.crafted = true
			used[it.base.id] = true
			out.append(it)
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
	if hero == null:
		return out
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
	var cid: StringName = hero.cls.id if hero.cls else &""
	if it.base.category != &"accessory":
		out.append(["Made for your class" if ItemGenerator.class_fit(it.base, cid) else "Not your class's usual gear", ItemGenerator.class_fit(it.base, cid)])
	var err := hero.equipment.check(it, hero.equipment.auto_slot(it), lvl, attrs)
	out.append(["You can wear it now" if err == "" else "Not yet wearable: %s" % err, err == ""])
	return out

## Close the trade. choice = index of the offer to take, or -1 for the gold. Returns {ok, error, item, gold, line}.
static func accept(hero: HeroData, items: Array, appraisal: Dictionary, choice: int) -> Dictionary:
	var res := {"ok": false, "error": "", "item": null, "gold": 0, "line": ""}
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
		if hero.inventory.add(got) > 0 or hero.inventory.index_of(got) < 0:
			# no room (cannot happen: the traded items just freed their cells) — undo
			for it: ItemInstance in items:
				hero.inventory.add(it)
			res.error = "Your bag is full."
			return res
		res.item = got
		res.line = DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.AFTER_ITEM, rng), got, who)
	hero.inventory.changed.emit()
	res.ok = true
	return res
