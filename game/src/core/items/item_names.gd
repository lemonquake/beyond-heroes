class_name ItemNames
## Gacha names for gear (bh-012). Every Licensed-or-better piece gets its own proper name and an epithet, rolled once
## from its generation seed and saved with it: "Vornhald, Oath of the Last Flame", "Kestmoor, the Storm's Promise".
## The epithet speaks for what the item is — its element, its strongest enchantment or its power — so two items of the
## same base almost never share a name. Stars (1–5) rate how close its rolls came to perfect.

const MIN_RARITY := BH.Rarity.LICENSED
const STAR_EDGES := [0.3, 0.5, 0.68, 0.85]      # score below edge i -> i + 1 stars; at or above the last -> 5

## [proper name, epithet] for a freshly generated item.
static func roll(it: ItemInstance, rng: RandomNumberGenerator) -> Array:
	return [proper(rng), epithet(it, rng)]

static func proper(rng: RandomNumberGenerator) -> String:
	var tries := 0
	while true:
		var n: String = _pick(DataRelics.ONSET, rng) + _pick(DataRelics.MIDDLE, rng) + _pick(DataRelics.CODA, rng)
		tries += 1
		if (n.length() >= 5 and n.length() <= 11) or tries > 8:
			return n.capitalize().replace(" ", "")
	return "Nameless"

static func epithet(it: ItemInstance, rng: RandomNumberGenerator) -> String:
	var cat := it.base.category
	var nouns: Array = DataRelics.NOUNS.get(cat, DataRelics.NOUNS[&"accessory"])
	var noun: String = _pick(nouns, rng)
	# a power speaks first ("Pyrelord's Oath"), then the element, then the strongest enchantment
	for i in range(it.powers.size() - 1, -1, -1):
		var p := DB.power(StringName(it.powers[i]))
		if p != null and p.tier != &"relic" and rng.randf() < 0.7:
			var pn := p.display_name
			return "%s %s" % [pn, noun] if pn.ends_with("'s") else "%s of %s" % [noun, pn]
	var theme := _theme_word(it, rng)
	match rng.randi_range(0, 3):
		0: return "%s of the %s" % [noun, theme]
		1: return "the %s's %s" % [theme, noun]
		2: return "%s of %s" % [noun, theme]
	return "%s of the %s" % [noun, theme]

static func _theme_word(it: ItemInstance, rng: RandomNumberGenerator) -> String:
	var el := it.base.element
	var best_stat: StringName = &""
	var best := -1.0
	for a in it.affixes:
		var d := DB.affix(StringName(a.id))
		if d == null:
			continue
		var s := String(d.stat)
		for prefix in ["added_", "dmg_", "res_", "pen_"]:
			if s.begins_with(prefix):
				var k := StringName(s.substr(prefix.length()))
				if DataRelics.ELEMENT_WORDS.has(k) and el == Elements.PHYSICAL:
					el = Elements.from_key(k)
		var w := float(a.get("tier", 0)) + float(a.value) / maxf(0.001, absf(float(d.tiers[d.tiers.size() - 1][2])))
		if DataRelics.STAT_WORDS.has(d.stat) and w > best:
			best = w
			best_stat = d.stat
	if el != Elements.PHYSICAL:
		var ek := Elements.key(el)
		if DataRelics.ELEMENT_WORDS.has(ek) and rng.randf() < 0.75:
			return _pick(DataRelics.ELEMENT_WORDS[ek], rng)
	if best_stat != &"" and rng.randf() < 0.8:
		return _pick(DataRelics.STAT_WORDS[best_stat], rng)
	return _pick(DataRelics.PLAIN_WORDS, rng)

static func _pick(list: Array, rng: RandomNumberGenerator) -> String:
	return String(list[rng.randi_range(0, list.size() - 1)])

# ---- Stars ---------------------------------------------------------------------------------------------------------

## 0..1: how good the rolls are — each enchantment's tier (against the best its item level allows) and value within
## that tier, plus the base quality roll.
static func score(it: ItemInstance) -> float:
	if it == null or not it.is_equipment():
		return 0.0
	var rule: Array = ItemGenerator.RULES[clampi(it.rarity, 0, ItemGenerator.RULES.size() - 1)]
	var qmax := float(rule[5])
	var qfrac := clampf(it.quality / qmax, 0.0, 1.0) if qmax > 0.0 else 0.5
	if it.affixes.is_empty():
		return qfrac * 0.6
	var total := 0.0
	var n := 0
	for a in it.affixes:
		var d := DB.affix(StringName(a.id))
		if d == null:
			continue
		var allowed := d.allowed_tiers(it.ilvl)
		var tier := int(a.get("tier", 0))
		var tfrac := float(allowed.find(tier) + 1) / float(maxi(1, allowed.size())) if allowed.has(tier) else 0.5
		var t: Array = d.tiers[clampi(tier, 0, d.tiers.size() - 1)]
		var span := float(t[2]) - float(t[1])
		var vfrac := clampf((float(a.value) - float(t[1])) / span, 0.0, 1.0) if absf(span) > 0.0001 else 1.0
		total += tfrac * 0.45 + vfrac * 0.55
		n += 1
	var aff := total / float(maxi(1, n))
	return clampf(aff * 0.85 + qfrac * 0.15, 0.0, 1.0)

static func stars(it: ItemInstance) -> int:
	if it == null or not it.is_equipment() or it.rarity < BH.Rarity.BASIC:
		return 0
	var s := score(it)
	for i in STAR_EDGES.size():
		if s < STAR_EDGES[i]:
			return i + 1
	return 5

## Every enchantment at the top tier its item level allows and within 2% of that tier's maximum.
static func is_perfect(it: ItemInstance) -> bool:
	if it == null or it.affixes.size() < 2:
		return false
	for a in it.affixes:
		var d := DB.affix(StringName(a.id))
		if d == null:
			return false
		var allowed := d.allowed_tiers(it.ilvl)
		if allowed.is_empty() or int(a.get("tier", 0)) != allowed[allowed.size() - 1]:
			return false
		var t: Array = d.tiers[int(a.tier)]
		var span := float(t[2]) - float(t[1])
		if absf(span) > 0.0001 and (float(a.value) - float(t[1])) / span < 0.98:
			return false
	return true

static func star_text(n: int) -> String:
	return "★".repeat(n) + "☆".repeat(maxi(0, 5 - n))

static func star_color(n: int) -> Color:
	return [Color(0.6, 0.6, 0.6), Color(0.7, 0.8, 0.7), Color(0.55, 0.85, 1.0), Color(0.85, 0.6, 1.0), Color(1.0, 0.8, 0.3)][clampi(n - 1, 0, 4)]
