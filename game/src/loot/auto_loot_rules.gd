class_name AutoLootRules
## Pure rules shared by the pickup system and filter preview. Exclusions win;
## quest/unique exceptions skip item filters, never capacity or load limits.

const CATEGORIES := {"weapons": "Weapons", "shields": "Shields", "armor": "Armor", "accessories": "Accessories",
	"ingredients": "Ingredients & Materials", "crystals": "Crystals", "potions": "Potions", "scrolls": "Scrolls & Town Portals",
	"consumables": "Other Consumables", "quest": "Keys & Quest Items", "other": "Other Items"}
const PRESETS := ["Everything", "Equipment", "Crafting supplies", "Potions & scrolls", "Valuable equipment"]

static func category(item: ItemInstance) -> String:
	match item.base.category:
		&"weapon": return "weapons"
		&"shield": return "shields"
		&"accessory": return "accessories"
		&"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots": return "armor"
		&"material": return "ingredients"
		&"crystal": return "crystals"
		&"quest": return "quest"
		&"consumable":
			if Inventory.is_scroll(item): return "scrolls"
			if Inventory.is_potion(item): return "potions"
			return "consumables"
	return "other"

static func preset(index: int) -> Dictionary:
	var rules := {"categories": {}, "min_rarity": 0}
	var allowed: Array = []
	match index:
		1, 4: allowed = ["weapons", "shields", "armor", "accessories"]
		2: allowed = ["ingredients", "crystals", "scrolls"]
		3: allowed = ["potions", "scrolls", "consumables"]
	for key in CATEGORIES:
		rules.categories[key] = allowed.is_empty() or key in allowed
	if index == 4:
		rules.min_rarity = BH.Rarity.ELITE
	return rules

static func _name_matches(item: ItemInstance, terms: String) -> bool:
	var hay := (item.display_name() + " " + String(item.base.id) + " " + item.base.display_name).to_lower()
	for term in terms.split(",", false):
		if term.strip_edges() != "" and term.strip_edges().to_lower() in hay:
			return true
	return false

## Empty string means accepted; otherwise a readable reason for leaving the drop.
static func item_reason(item: ItemInstance, hero: HeroData, rules: Dictionary, legacy_rarity := 0) -> String:
	if item == null: return "No item"
	if _name_matches(item, String(rules.get("exclude", ""))): return "Excluded name"
	if bool(rules.get("always_quest", false)) and item.base.is_quest(): return ""
	if bool(rules.get("always_unique", false)) and (item.base.unique_name != "" or item.base.set_id != &""): return ""
	var categories: Dictionary = rules.get("categories", {})
	if not bool(categories.get(category(item), true)): return "Category disabled"
	if item.rarity < int(rules.get("min_rarity", legacy_rarity)): return "Below minimum rarity"
	var include := String(rules.get("include", "")).strip_edges()
	if include != "" and not _name_matches(item, include): return "Name does not match"
	if item.is_equipment():
		if item.ilvl < int(rules.get("min_level", 0)): return "Below minimum item level"
		if bool(rules.get("usable_only", false)) and hero:
			if not item.unbound and item.required_level() > hero.progress.level: return "Level requirement too high"
			var attrs := hero.progress.base_attributes()
			for attr in item.base.requirements:
				if float(attrs.get(attr, 0)) < float(item.base.requirements[attr]): return "Attribute requirements not met"
		if item.sockets < int(rules.get("min_sockets", 0)): return "Not enough sockets"
		if item.base.is_weapon():
			var types: Dictionary = rules.get("weapon_types", {})
			if not bool(types.get(String(item.base.weapon_type), true)): return "Weapon type disabled"
	if item.base_value() < int(rules.get("min_value", 0)): return "Below minimum item value"
	var max_weight := float(rules.get("max_weight", 0.0))
	if max_weight > 0 and item.weight() > max_weight: return "Stack is too heavy"
	var ratio := float(rules.get("min_value_weight", 0.0))
	if ratio > 0 and item.weight() > 0 and float(item.base_value() * item.count) / item.weight() < ratio: return "Value per weight too low"
	var cap := int(rules.get("consumable_cap", 0))
	if cap > 0 and hero and item.base.is_consumable() and hero.inventory.count_of(item.base.id) + item.count > cap:
		return "Consumable limit reached"
	return ""

static func pickup_reason(item: ItemInstance, hero: HeroData, stats: DerivedStats, rules: Dictionary, legacy_rarity := 0) -> String:
	var reason := item_reason(item, hero, rules, legacy_rarity)
	if reason != "": return reason
	if hero == null or not hero.inventory.can_fit(item): return "No room in bags"
	var reserve := clampi(int(rules.get("reserve_slots", 0)), 0, Inventory.BAG_CAPACITY)
	if reserve > 0:
		var trial := hero.inventory.copy()
		trial.add(item.clone())
		if trial.free_cells() < reserve and trial.free_cells() < hero.inventory.free_cells(): return "Keeping bag slots free"
	if stats:
		var limit := clampf(float(rules.get("max_load", 100.0)), 1.0, 100.0) / 100.0
		if stats.get_stat(&"carry_weight") + item.weight() > stats.get_stat(&"carry_capacity") * limit:
			return "Carrying limit reached"
	return ""

static func summary(rules: Dictionary, legacy_rarity := 0) -> String:
	var names := []
	var categories: Dictionary = rules.get("categories", {})
	for key in CATEGORIES:
		if bool(categories.get(key, true)): names.append(CATEGORIES[key])
	var rarity := clampi(int(rules.get("min_rarity", legacy_rarity)), 0, BH.RARITY_COUNT - 1)
	return "%s · %s and better" % ["All categories" if names.size() == CATEGORIES.size() else (", ".join(names) if not names.is_empty() else "No categories"), BH.RARITY_NAMES[rarity]]
