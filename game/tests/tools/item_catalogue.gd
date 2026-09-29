extends Node
## bh-018: writes docs/ITEM_CATALOGUE.txt — every item and piece of equipment in Beyond Heroes, straight from the game's
## own data (DB, DataItems, DataCrystals, DataUpgrades, DataCrafting, DataShops), so it never drifts from the code.
##   godot --headless --path game res://tests/tools/item_catalogue.tscn [-- --out=<path>]

var L := PackedStringArray()

func _ready() -> void:
	var out := ProjectSettings.globalize_path("res://").path_join("../docs/ITEM_CATALOGUE.txt")
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	_write()
	var f := FileAccess.open(out, FileAccess.WRITE)
	f.store_string("\n".join(L) + "\n")
	f.close()
	print("CATALOGUE %d lines -> %s" % [L.size(), out])
	get_tree().quit()

# ---- helpers -------------------------------------------------------------------------------------------------------

func _h1(t: String) -> void:
	L.append("")
	L.append("=".repeat(118))
	L.append(t.to_upper())
	L.append("=".repeat(118))

func _h2(t: String) -> void:
	L.append("")
	L.append(t)
	L.append("-".repeat(t.length()))

func _p(t := "") -> void:
	L.append(t)

func _wrap(t: String, indent := "", width := 116) -> void:
	var line := indent
	for w in t.split(" "):
		if line.length() + w.length() + 1 > width and line.strip_edges() != "":
			L.append(line)
			line = indent
		line += ("" if line.strip_edges() == "" else " ") + w
	if line.strip_edges() != "":
		L.append(line)

static func _pad(s: String, n: int) -> String:
	return s.substr(0, n) if s.length() >= n else s + " ".repeat(n - s.length())

static func _row(cols: Array, widths: Array) -> String:
	var s := ""
	for i in cols.size():
		s += _pad(str(cols[i]), int(widths[i])) + (" " if i < cols.size() - 1 else "")
	return s.strip_edges(false, true)

static func _mods(arr: Array) -> String:
	var out := PackedStringArray()
	for m in arr:
		out.append(StatDefs.format_modifier(m.stat, m.op, m.value))
	return "; ".join(out)

static func _reqs(b: ItemBaseDef) -> String:
	var out := PackedStringArray()
	for a in b.requirements:
		out.append("%d %s" % [int(b.requirements[a]), String(a).to_upper()])
	return " ".join(out) if not out.is_empty() else "-"

static func _thousands(n: int) -> String:
	var s := str(absi(n))
	var o := ""
	while s.length() > 3:
		o = "," + s.substr(s.length() - 3) + o
		s = s.substr(0, s.length() - 3)
	return s + o

func _bases(filter: Callable) -> Array:
	var out: Array = []
	for b in DB.item_bases.values():
		if filter.call(b):
			out.append(b)
	out.sort_custom(func(a: ItemBaseDef, b: ItemBaseDef) -> bool:
		if a.level_req != b.level_req:
			return a.level_req < b.level_req
		return a.display_name < b.display_name)
	return out

# ---- the catalogue -------------------------------------------------------------------------------------------------

func _write() -> void:
	var total := DB.item_bases.size()
	_p("BEYOND HEROES — ITEM AND EQUIPMENT CATALOGUE")
	_p("Generated from the game's data by game/tests/tools/item_catalogue.gd (%s). %d item bases." % [Time.get_date_string_from_system(), total])
	_p("Regenerate: \"C:/Users/Lemon PC/Desktop/Godot.exe\" --headless --path game res://tests/tools/item_catalogue.tscn")
	_p("")
	_p("Contents")
	for s in ["1. Rarity tiers, equipment slots, weight and sockets", "2. Weapons", "3. Shields", "4. Armour (helms, inner garments, armour, gloves, boots)",
			"5. Accessories", "6. Item sets", "7. Named uniques", "8. Enchantments (random affixes)", "9. Powers (mythical, legendary, aether, relic)",
			"10. Faction licenses", "11. Socket crystals and the Socket Specialists", "12. Weapon upgrades: Enchantment and Fore-Tech",
			"13. Consumables", "14. Materials, currencies and relic caches", "15. Quest items", "16. Crafting recipes", "17. Where to buy: merchants"]:
		_p("  " + s)
	_rarity()
	_weapons()
	_shields()
	_armour()
	_accessories()
	_sets()
	_uniques()
	_affixes()
	_powers()
	_licenses()
	_crystals()
	_upgrades()
	_consumables()
	_materials()
	_quest()
	_recipes()
	_shops()

func _rarity() -> void:
	_h1("1. Rarity tiers, equipment slots, weight and sockets")
	_p(_row(["Tier", "Name", "Max sockets", "Loot beam", "What it means"], [4, 10, 11, 9, 80]))
	for r in BH.RARITY_COUNT:
		_p(_row([r, BH.RARITY_NAMES[r], DataCrystals.MAX_SOCKETS[r], "%.1f m" % BH.RARITY_BEAM[r], BH.RARITY_DESC[r]], [4, 10, 11, 9, 80]))
	_h2("Equipment slots")
	for s in BH.SLOTS:
		var cats := PackedStringArray()
		for c in BH.CATEGORY_SLOTS:
			if (BH.CATEGORY_SLOTS[c] as Array).has(s):
				cats.append(String(c))
		_p("  %s — takes: %s" % [_pad(BH.SLOT_NAMES[s], 14), ", ".join(cats)])
	_h2("Carried weight")
	_wrap("Everything worn and carried has weight. Carry capacity = (%d + %.1f x Strength + bonuses). Up to %d%% load there is no slowdown; at 100%% load movement is %d%% slower; above 100%% the hero is Overburdened (%d%% slower, no dodging). (bh-018: capacity doubled from 55 + 1.6 per Strength.)" % [
		roundi(StatCalculator.CARRY_BASE), StatCalculator.CARRY_PER_STR, roundi(StatCalculator.LOAD_FREE * 100), roundi(StatCalculator.LOAD_SLOW_MAX * 100), roundi(StatCalculator.OVERBURDEN_SLOW * 100)], "  ")

func _weapons() -> void:
	_h1("2. Weapons")
	var types := {}
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.is_weapon()):
		if not types.has(b.weapon_type):
			types[b.weapon_type] = []
		types[b.weapon_type].append(b)
	var order := types.keys()
	order.sort_custom(func(a, b) -> bool: return String(a) < String(b))
	for wt_id in order:
		var wt := DB.weapon_type(wt_id)
		_h2("%s (%d)" % [wt.display_name if wt else String(wt_id).capitalize(), (types[wt_id] as Array).size()])
		if wt:
			_wrap("%s%s. Base %.2f attacks/s, %d%% crit, %.1f m reach, heavy x%.1f." % ["Two-handed" if wt.two_handed else "One-handed",
				", ranged" if wt.ranged else "", wt.attacks_per_second, roundi(wt.crit_chance * 100), wt.reach, wt.heavy_multiplier], "  ")
		_p(_row(["  Lvl", "Name", "Damage", "APS", "Element", "Requires", "Wt", "Value", "Class", "Notes"], [5, 26, 9, 5, 14, 16, 5, 6, 11, 40]))
		for b: ItemBaseDef in types[wt_id]:
			var el := "-"
			if b.element != Elements.PHYSICAL and b.element_share > 0.0:
				el = "%d%% %s" % [roundi(b.element_share * 100), Elements.NAMES[b.element]]
			var note := _mods(b.implicit)
			if b.unique_name != "":
				note = ("Unique. " + note).strip_edges()
			if b.set_id != &"":
				note = ("Set: %s. %s" % [DB.item_set(b.set_id).display_name if DB.item_set(b.set_id) else String(b.set_id), note]).strip_edges()
			_p(_row(["  %d" % b.level_req, b.unique_name if b.unique_name != "" else b.display_name, "%d-%d" % [roundi(b.damage_min), roundi(b.damage_max)],
				"%.2f" % b.weapon_aps(), el, _reqs(b), "%.1f" % b.weight, b.value, String(b.class_hint), note], [5, 26, 9, 5, 14, 16, 5, 6, 11, 60]))

func _shields() -> void:
	_h1("3. Shields")
	_p(_row(["  Lvl", "Name", "Def", "Block", "Strength", "Requires", "Wt", "Value", "Notes"], [5, 26, 5, 6, 9, 16, 5, 6, 50]))
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.category == &"shield"):
		_p(_row(["  %d" % b.level_req, b.unique_name if b.unique_name != "" else b.display_name, roundi(b.defense), "%d%%" % roundi(b.block_chance * 100),
			"%d%%" % roundi(b.block_strength * 100), _reqs(b), "%.1f" % b.weight, b.value, _mods(b.implicit)], [5, 26, 5, 6, 9, 16, 5, 6, 60]))

func _armour() -> void:
	_h1("4. Armour")
	for cat in [&"helm", &"inner_garment", &"armor", &"gloves", &"boots"]:
		var list := _bases(func(b: ItemBaseDef) -> bool: return b.category == cat)
		_h2("%s (%d)" % [{&"helm": "Helms", &"inner_garment": "Inner garments", &"armor": "Body armour", &"gloves": "Gloves", &"boots": "Boots"}[cat], list.size()])
		_p(_row(["  Lvl", "Name", "Weight class", "Def", "Requires", "Wt", "Value", "Notes"], [5, 28, 12, 5, 16, 5, 6, 60]))
		for b: ItemBaseDef in list:
			var note := _mods(b.implicit)
			if b.set_id != &"":
				note = ("Set: %s. %s" % [DB.item_set(b.set_id).display_name if DB.item_set(b.set_id) else String(b.set_id), note]).strip_edges()
			if b.unique_name != "":
				note = ("Unique. " + note).strip_edges()
			_p(_row(["  %d" % b.level_req, b.unique_name if b.unique_name != "" else b.display_name, String(b.weight_class), roundi(b.defense), _reqs(b),
				"%.1f" % b.weight, b.value, note], [5, 28, 12, 5, 16, 5, 6, 70]))

func _accessories() -> void:
	_h1("5. Accessories (rings, amulets, charms)")
	_p(_row(["  Lvl", "Name", "Wt", "Value", "Implicit"], [5, 28, 5, 6, 70]))
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.category == &"accessory"):
		var note := _mods(b.implicit)
		if b.unique_name != "":
			note = ("Unique. " + note).strip_edges()
		_p(_row(["  %d" % b.level_req, b.unique_name if b.unique_name != "" else b.display_name, "%.1f" % b.weight, b.value, note], [5, 28, 5, 6, 80]))

func _sets() -> void:
	_h1("6. Item sets")
	_wrap("Set pieces always drop at Master tier or better. Wearing several different pieces of one set unlocks its bonuses.", "  ")
	var ids := DB.item_sets.keys()
	ids.sort_custom(func(a, b) -> bool: return String(a) < String(b))
	for sid in ids:
		var sd: SetDef = DB.item_sets[sid]
		_h2(sd.display_name + (" (%s)" % String(sd.class_hint) if sd.class_hint != &"" else ""))
		var names := PackedStringArray()
		for pid in sd.pieces:
			var b := DB.item_base(StringName(pid))
			names.append("%s [%s]" % [b.display_name if b else String(pid), String(b.category) if b else "?"])
		_wrap("Pieces: " + ", ".join(names), "  ")
		for n in sd.thresholds():
			_wrap("(%d) %s" % [n, sd.bonuses[n].get("desc", "")], "  ")
		if sd.lore != "":
			_wrap(sd.lore, "  ")

func _uniques() -> void:
	_h1("7. Named uniques")
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.unique_name != ""):
		_h2("%s — %s, level %d (%s)" % [b.unique_name, b.display_name, b.level_req, BH.rarity_name(b.fixed_rarity) if b.fixed_rarity >= 0 else "any"])
		var parts := PackedStringArray()
		if b.is_weapon():
			parts.append("%d-%d damage" % [roundi(b.damage_min), roundi(b.damage_max)])
		elif b.defense > 0.0:
			parts.append("%d defense" % roundi(b.defense))
		if not b.implicit.is_empty():
			parts.append(_mods(b.implicit))
		if not b.fixed_mods.is_empty():
			parts.append(_mods(b.fixed_mods))
		_wrap("; ".join(parts), "  ")
		for pid in b.fixed_powers:
			var p := DB.power(StringName(pid))
			if p:
				_wrap("%s: %s" % [p.display_name, p.description], "  ")
		if b.lore != "":
			_wrap(b.lore, "  ")

func _affixes() -> void:
	_h1("8. Enchantments (random affixes)")
	_wrap("Basic items roll one enchantment, Advanced two, and higher tiers more and stronger ones. Each enchantment has level-gated tiers: [min item level: min-max].", "  ")
	var ids := DB.affix_defs.keys()
	ids.sort_custom(func(a, b) -> bool: return String(a) < String(b))
	_p(_row(["  Name", "Pre/suf", "Stat", "Tiers", "Fits"], [22, 7, 26, 44, 40]))
	for id in ids:
		var a: AffixDef = DB.affix_defs[id]
		var tiers := PackedStringArray()
		for t in a.tiers:
			var pct := StatDefs.fmt_of(a.stat) == StatDefs.Fmt.PCT or a.op != StatModifier.Op.FLAT or String(a.stat).begins_with("local_")
			tiers.append("[%d: %s-%s]" % [int(t[0]), ("%d%%" % roundi(float(t[1]) * 100)) if pct else str(snappedf(float(t[1]), 0.1)),
				("%d%%" % roundi(float(t[2]) * 100)) if pct else str(snappedf(float(t[2]), 0.1))])
		var cats := "all equipment" if a.categories.is_empty() else ", ".join(PackedStringArray(a.categories.map(func(c): return String(c))))
		_p(_row(["  " + a.label, "prefix" if a.is_prefix else "suffix", StatDefs.name_of(a.stat), " ".join(tiers), cats], [22, 7, 26, 44, 60]))

func _powers() -> void:
	_h1("9. Powers")
	for tier in [&"mythical", &"legendary", &"aether", &"relic"]:
		_h2(String(tier).capitalize() + " powers")
		var ids := DB.power_defs.keys()
		ids.sort_custom(func(a, b) -> bool: return String(a) < String(b))
		for id in ids:
			var p: LegendaryPowerDef = DB.power_defs[id]
			if p.tier != tier:
				continue
			var cats := "any slot" if p.categories.is_empty() else ", ".join(PackedStringArray(p.categories.map(func(c): return String(c))))
			_wrap("%s%s — %s (%s)" % [p.display_name, " [%s]" % String(p.class_hint) if p.class_hint != &"" else "", p.description, cats], "  ")

func _licenses() -> void:
	_h1("10. Faction licenses")
	_wrap("Licensed-tier equipment carries one guild license: fixed specialisation bonuses that grow with item level (value at item level 1, + per level).", "  ")
	for lid in DB.licenses:
		var lic: Dictionary = DB.licenses[lid]
		var parts := PackedStringArray()
		for m in lic.get("mods", []):
			parts.append("%s (+%s/level)" % [StatDefs.format_modifier(StringName(m[0]), int(m[1]), float(m[2])), str(snappedf(float(m[3]), 0.0001))])
		_wrap("%s: %s" % [lic.get("name", String(lid)), "; ".join(parts)], "  ")

func _crystals() -> void:
	_h1("11. Socket crystals and the Socket Specialists (bh-018)")
	_wrap("Every piece of equipment can have sockets opened by a Socket Specialist: Ysolde Marr (Marr's Lapidary, Malasugue), Anselm Cray (Cray's Cutting Room, Olivar) and Dagna Flint (Flint's Crystal Cart, Wyman Outpost). The most sockets a piece can hold depends on its tier (section 1): from 1 (Beginner, Common) to 7 (Aether).", "  ")
	_h2("Services")
	_wrap("Add Socket — opens one more socket. Fee = %d x (sockets after opening)^2 x (1 + item level / 20)." % roundi(Sockets.ADD_FEE), "  ")
	_wrap("Remove Socket — closes an empty socket. Fee = %d x open sockets x (1 + item level / 20)." % roundi(Sockets.REMOVE_FEE), "  ")
	_wrap("Set Crystal — free. A set crystal stays until the piece is purged or crystallized.", "  ")
	_wrap("Purge — breaks every crystal out of the piece: the crystals are destroyed, the piece keeps its (now empty) sockets. Fee = %d x crystals x (1 + item level / 20)." % roundi(Sockets.PURGE_FEE), "  ")
	_wrap("Crystallization — destroys the piece; every crystal set in it returns to the bag. Fee = %d%% of the crystals' shop value (at least 100)." % roundi(Sockets.CRYSTALLIZE_SHARE * 100), "  ")
	_p("")
	_p("  Example Add Socket fees for an item level 20 piece: " + ", ".join(PackedStringArray(range(1, 8).map(func(n): return "socket %d: %s" % [n, _thousands(roundi(Sockets.ADD_FEE * n * n * 2.0))]))))
	_h2("Where crystals come from")
	_wrap("Every boss always drops one crystal of any grade (higher grades grow likelier with the boss's level). Every miniboss (champion) always drops a Fragment or a Shard. Aetherift is rare: 4% of boss crystals, 1% of champion crystals. The three Specialists sell every family except Aetherift from 5,000 gold a Fragment (Shards, Crystallines and Orbitals unlock with hero level); Aetherift Fragments are sold at a higher level only.", "  ")
	_h2("Grades and prices")
	_p(_row(["  Grade", "Tier colour", "Shop price", "Aetherift price"], [15, 12, 11, 16]))
	for g in 4:
		_p(_row(["  " + DataCrystals.GRADE_NAMES[g], BH.rarity_name(DataCrystals.GRADE_RARITY[g]), _thousands(DataCrystals.PRICE[g]),
			_thousands(DataCrystals.PRICE[g] * DataCrystals.AETHER_PRICE_MULT)], [15, 12, 11, 16]))
	for f in DataCrystals.ORDER:
		var fd: Dictionary = DataCrystals.FAMILIES[f]
		_h2("%s — %s" % [fd.name, fd.blurb])
		for g in 4:
			var id := DataCrystals.id_of(f, g)
			_p("  %s (%s)" % [DataCrystals.name_of(f, g), id])
			for line in DataCrystals.describe(id):
				_wrap(line, "      ")

func _upgrades() -> void:
	_h1("12. Weapon upgrades: Enchantment and Fore-Tech")
	_wrap("Enchantment (at an Alchemy Table): a rune, rank I-III, turns a share of the weapon's damage into an element and adds elemental gifts. Fore-Tech (at a Forge): a mechanical refit +1..+%d, +%d%% weapon damage per rank plus its own bonus. Both can be on one weapon; a different rune or refit starts over at rank 1." % [DataUpgrades.TECH_MAX, roundi(DataUpgrades.TEMPER_PER_RANK * 100)], "  ")
	_h2("Enchantments")
	for id in DataUpgrades.enchant_ids():
		var e := DataUpgrades.enchant(id)
		var ranks := PackedStringArray()
		for r in range(1, DataUpgrades.ENCHANT_MAX + 1):
			ranks.append("%s: %d%% %s; %s" % [DataUpgrades.roman(r), roundi(DataUpgrades.enchant_share(id, r) * 100), Elements.NAMES[int(e.element)], _mods(DataUpgrades.enchant_mods(id, r))])
		_wrap("%s — %s" % [e.name, e.text], "  ")
		for s in ranks:
			_wrap(s, "      ")
	_h2("Fore-Tech refits")
	for id in DataUpgrades.tech_ids():
		var t := DataUpgrades.tech(id)
		_wrap("%s (best on %s) — %s Per rank: %s" % [t.name, t.best, t.text, _mods(DataUpgrades.tech_mods(id, 1))], "  ")

func _effect(b: ItemBaseDef) -> String:
	var e := b.consumable_effect
	var out := PackedStringArray()
	if e.has("heal"):
		out.append("restores %d%% HP" % roundi(float(e.heal) * 100))
	if e.has("mana"):
		out.append("restores %d%% Mana" % roundi(float(e.mana) * 100))
	if e.has("instant"):
		out.append("instantly")
	if e.has("buff"):
		var sd: Dictionary = StatusRules.DEFS.get(StringName(e.buff), {})
		out.append("%s for %ds: %s" % [sd.get("name", String(e.buff)), roundi(float(e.get("duration", sd.get("duration", 0.0)))), sd.get("desc", "")])
	if e.has("throw"):
		out.append("thrown")
	if e.has("portal"):
		out.append("opens a Town Portal")
	if e.has("return"):
		out.append("returns to Malasugue")
	if e.has("cleanse"):
		out.append("cleanses")
	if e.has("phoenix"):
		out.append("revives you once")
	return ", ".join(out)

func _consumables() -> void:
	_h1("13. Consumables")
	_p(_row(["  Lvl", "Name", "Stack", "Value", "Effect"], [5, 28, 6, 6, 70]))
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.is_consumable()):
		_p(_row(["  %d" % b.level_req, b.display_name, b.stack_max, b.value, b.flavor if b.flavor != "" else _effect(b)], [5, 28, 6, 6, 200]))

func _materials() -> void:
	_h1("14. Materials, currencies and relic caches")
	_p(_row(["  Name", "Stack", "Value", "Notes"], [30, 6, 6, 80]))
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.category == &"material" or (not b.is_consumable() and not b.is_quest() and not b.category in BH.CATEGORY_SLOTS and b.category != &"crystal")):
		_p(_row(["  " + b.display_name, b.stack_max, b.value, b.flavor], [30, 6, 6, 200]))

func _quest() -> void:
	_h1("15. Quest items")
	for b in _bases(func(b: ItemBaseDef) -> bool: return b.is_quest()):
		_wrap("%s — %s" % [b.display_name, b.flavor], "  ")

func _recipes() -> void:
	_h1("16. Crafting recipes")
	var groups := {}
	for r in DataCrafting.all():
		var g := String(r.get("group", "Other"))
		if not groups.has(g):
			groups[g] = []
		groups[g].append(r)
	var names := groups.keys()
	names.sort()
	for g in names:
		_h2(g)
		for r in groups[g]:
			var ins := PackedStringArray()
			for i in r.get("inputs", []):
				var b := DB.item_base(StringName(i[0]))
				ins.append("%d %s" % [int(i[1]), b.display_name if b else String(i[0])])
			var out_s := ""
			var o: Dictionary = r.get("out", {})
			if o.has("base"):
				var ob := DB.item_base(StringName(o.base))
				out_s = "%s%s" % [ob.display_name if ob else String(o.base), " x%d" % int(o.count) if int(o.get("count", 1)) > 1 else ""]
			_wrap("%s (level %d, %d gold, %s%s): %s -> %s" % [r.get("name", String(r.id)), int(r.get("level", 1)), int(r.get("gold", 0)),
				DataCrafting.station_names(r.get("stations", [])), "" if r.get("known", false) else ", needs its recipe scroll", ", ".join(ins), out_s], "  ")

func _shops() -> void:
	_h1("17. Where to buy: merchants")
	var ids := DB.shops.keys()
	ids.sort_custom(func(a, b) -> bool: return String(a) < String(b))
	for sid in ids:
		var sh: ShopDef = DB.shops[sid]
		var npc := DB.npc(sh.npc)
		_h2("%s — %s%s" % [sh.display_name, npc.display_name if npc else String(sh.npc), " (%s)" % DB.map_def(npc.map).display_name if npc and DB.map_def(npc.map) else ""])
		var fixed := PackedStringArray()
		for f in sh.fixed:
			var b := DB.item_base(StringName(f.base))
			fixed.append("%s%s" % [b.display_name if b else String(f.base), " (lvl %d+)" % int(f.level_min) if int(f.get("level_min", 1)) > 1 else ""])
		if not fixed.is_empty():
			_wrap("Always: " + ", ".join(fixed), "  ")
		for pl in sh.pools:
			_wrap("Rotating stock: %d x %s%s" % [int(pl.count), ", ".join(PackedStringArray((pl.categories as Array).map(func(c): return String(c)))),
				(" (%s)" % ", ".join(PackedStringArray((pl.get("weapon_types", []) as Array).map(func(c): return String(c))))) if pl.has("weapon_types") else ""], "  ")
		_wrap("Prices: x%.2f markup, buys at x%.2f%s." % [sh.markup, sh.sell_rate, "; restocks after every cleared stage or miniboss" if sh.restock_on_clears else ""], "  ")
