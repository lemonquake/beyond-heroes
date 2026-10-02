class_name LootPools
## bh-033: resolves the material and supply pools of a kill (layers, precedence and data in DataLootPools). Pure rules:
## Loot rolls the result, the audit tool and tests read the same resolution.

## Where a kill happens: {map, dungeon, theme}. Overworld maps have no dungeon or theme.
static func context_for_map(map_id: StringName) -> Dictionary:
	var dg: StringName = DataDungeons.parse(map_id)[0] if map_id != &"" else &""
	if dg != &"":
		return {"map": map_id, "dungeon": dg, "theme": StringName(DataDungeons.get_def(dg).get("theme", ""))}
	return {"map": map_id, "dungeon": &"", "theme": &""}

## The composed pool of a dungeon: its theme inherited, signature material added, then its own add/weight/exclude.
static func dungeon_pool(dungeon: StringName) -> Array:
	var def := DataDungeons.get_def(dungeon)
	if def.is_empty():
		return []
	var mods: Dictionary = DataLootPools.DUNGEON.get(dungeon, {})
	var excl: Array = mods.get("exclude", [])
	var rows := []
	for e in DataLootPools.THEME.get(StringName(def.get("theme", "")), []):
		if not excl.has(e[0]):
			rows.append(_row(e, "theme"))
	var sig := StringName(def.get("material", ""))
	if sig != &"":
		var found := false
		for r in rows:
			if r.id == sig:
				r.chance = maxf(float(r.chance), DataLootPools.SIGNATURE_CHANCE)
				r.layer = "signature"
				found = true
		if not found:
			rows.append({"id": sig, "chance": DataLootPools.SIGNATURE_CHANCE, "min": 1, "max": 1, "layer": "signature"})
	for e in mods.get("add", []):
		if not rows.any(func(r): return r.id == e[0]):
			rows.append(_row(e, "dungeon"))
	var w: Dictionary = mods.get("weight", {})
	for r in rows:
		r.chance = clampf(float(r.chance) * float(w.get(r.id, 1.0)), 0.0, 1.0)
	return rows

static func _row(e: Array, layer: String) -> Dictionary:
	return {"id": StringName(e[0]), "chance": float(e[1]), "min": int(e[2]), "max": int(e[3]), "layer": layer}

## Every material/supply entry of `def` in `ctx`, each item at most once: monster table first (never removed or
## doubled), then family, then dungeon (theme + signature + own) or overworld map layer.
static func resolve(def: EnemyDef, ctx: Dictionary) -> Array:
	var out := []
	var seen := {}
	for e in def.loot:
		var r := _row(e, "monster")
		out.append(r)
		seen[r.id] = true
	for e in DataLootPools.FAMILY.get(def.family, []):
		if (e as Array).size() > 4 and e[4] == "metal" and def.body_shape != &"humanoid":
			continue
		if not seen.has(StringName(e[0])):
			out.append(_row(e, "family"))
			seen[StringName(e[0])] = true
	var place: Array = dungeon_pool(StringName(ctx.get("dungeon", ""))) if StringName(ctx.get("dungeon", "")) != &"" \
		else DataLootPools.MAP.get(StringName(ctx.get("map", "")), []).map(func(e): return _row(e, "map"))
	for r in place:
		if not seen.has(r.id):
			out.append(r)
			seen[r.id] = true
	return out

## Roll a resolved pool: [[base id, count], ...]. Quest items drop only while the hero holds fewer than the entry's
## maximum (a keepsake, never bag clutter). Progression staples (DataLootPools.PITY) carry bounded bad-luck protection
## in hero.loot_pity.
static func roll(entries: Array, rng: RandomNumberGenerator, hero: HeroData) -> Array:
	var out := []
	for r in entries:
		var b := DB.item_base(r.id)
		if b == null:
			continue
		if b.is_quest() and hero != null and hero.inventory.count_of(r.id) >= int(r.max):
			continue
		var hit := rng.randf() < float(r.chance)
		if DataLootPools.PITY.has(r.id) and hero != null:
			var misses := int(hero.loot_pity.get(String(r.id), 0))
			if not hit and misses + 1 >= int(DataLootPools.PITY[r.id]):
				hit = true
			hero.loot_pity[String(r.id)] = 0 if hit else misses + 1
		if hit:
			out.append([r.id, rng.randi_range(int(r.min), maxi(int(r.min), int(r.max)))])
	return out

## Expected units of `item` per kill of `def` in `ctx` (no pity), for the supply audit.
static func expected(def: EnemyDef, ctx: Dictionary, item: StringName) -> float:
	for r in resolve(def, ctx):
		if r.id == item:
			return float(r.chance) * (float(r.min) + float(r.max)) * 0.5
	return 0.0

## A dungeon lord's or usurper's completion supplies: [[base id, count], ...], counts growing with the dungeon tier.
static func completion(dungeon: StringName, usurper: bool, rng: RandomNumberGenerator) -> Array:
	var def := DataDungeons.get_def(dungeon)
	if def.is_empty():
		return []
	var tier := maxi(1, int(def.get("tier", 1)))
	var rows: Array = DataLootPools.USURPER_COMPLETION if usurper else DataLootPools.BOSS_COMPLETION
	return _fixed(rows, StringName(def.get("material", "")), 1.0 + 0.25 * float(tier - 1), rng)

## A dungeon chest's supplies (chest tier 0..2).
static func chest_supply(dungeon: StringName, tier: int, rng: RandomNumberGenerator) -> Array:
	var def := DataDungeons.get_def(dungeon)
	var sig := StringName(def.get("material", "")) if not def.is_empty() else &""
	return _fixed(DataLootPools.CHEST_SUPPLY[clampi(tier, 0, 2)], sig, 1.0, rng)

static func _fixed(rows: Array, signature: StringName, scale: float, rng: RandomNumberGenerator) -> Array:
	var out := []
	for e in rows:
		var id: StringName = signature if e[0] == &"signature" else StringName(e[0])
		if id == &"" or DB.item_base(id) == null:
			continue
		out.append([id, maxi(1, roundi(float(rng.randi_range(int(e[1]), int(e[2]))) * scale))])
	return out

## Short "where to find it" hints for an ingredient, from the resolved pools (used by crafting tooltips). Cached.
static var _hints := {}

static func source_hint(item: StringName) -> String:
	if _hints.is_empty():
		_build_hints()
	return String(_hints.get(item, ""))

## Plain family names for hints, in the order a new hero meets them.
const FAMILY_NAMES := {&"bandit": "bandits", &"goblin": "goblins", &"orc": "orcs", &"undead": "armed skeletons", &"beast": "beasts",
	&"ogre": "ogres", &"cultist": "cultists", &"construct": "constructs", &"corrupted": "corrupted beasts", &"fungal": "fungal creatures",
	&"aether": "Aether spirits", &"drowned": "the drowned", &"kharvenn": "Kharvenn", &"gigas": "gigas", &"wirewright": "wirewrights",
	&"wiresick": "the wiresick", &"infernal": "infernals", &"jade": "jade guardians"}

static func _build_hints() -> void:
	var parts := {}
	# family salvage first: "Carried by bandits, goblins, orcs and other armed foes"
	var fam_by_item := {}
	for fam in FAMILY_NAMES:
		for e in DataLootPools.FAMILY.get(fam, []):
			(fam_by_item.get_or_add(StringName(e[0]), []) as Array).append(FAMILY_NAMES[fam])
	for id in fam_by_item:
		var names: Array = fam_by_item[id]
		var metal := DataLootPools.FAMILY.values().any(func(rows): return rows.any(func(e): return e[0] == id and (e as Array).size() > 4))
		(parts.get_or_add(id, []) as Array).append("Carried by %s%s" % [", ".join(names.slice(0, 3)),
			(" and other armed foes" if metal else " and others") if names.size() > 3 else ""])
	# then the monsters whose own table lists it (the likeliest two)
	var by_item := {}
	for def: EnemyDef in DB.enemies.values():
		if def.archetype == &"boss":
			continue
		for e in def.loot:
			(by_item.get_or_add(StringName(e[0]), []) as Array).append([float(e[1]) * (float(e[2]) + float(e[3])) * 0.5, def.display_name])
	for id in by_item:
		if fam_by_item.has(id):
			continue
		var lst: Array = by_item[id]
		lst.sort_custom(func(a, b): return a[0] > b[0] or (a[0] == b[0] and a[1] < b[1]))
		var names := []
		for x in lst:
			if not names.has(x[1]):
				names.append(x[1])
			if names.size() >= 2:
				break
		(parts.get_or_add(id, []) as Array).append("Dropped by %s" % ", ".join(names) + (" and others" if lst.size() > 2 else ""))
	for dg in DataDungeons.order():
		var d := DataDungeons.get_def(dg)
		var sig := StringName(d.get("material", ""))
		if sig != &"" and not (parts.get(sig, []) as Array).any(func(s): return s.begins_with("Signature")):
			(parts.get_or_add(sig, []) as Array).append("Signature of %s" % String(d.get("name", dg)))
	for r in DataCrafting.all():
		var o: Dictionary = r.out
		if o.has("base"):
			var ins := []
			for inp in r.inputs:
				var ib := DB.item_base(inp[0])
				ins.append("%s x%d" % [ib.display_name if ib else String(inp[0]), int(inp[1])])
			(parts.get_or_add(StringName(o.base), []) as Array).push_front("%s from %s" % [DataCrafting.station_names(r.stations), ", ".join(ins)])
	for h in [&"silverleaf", &"mirebloom", &"emberroot", &"brightcap"]:
		(parts.get_or_add(h, []) as Array).push_front("Gathered from herb patches")
	(parts.get_or_add(&"champion_essence", []) as Array).push_front("Every champion (miniboss) drops 1-2")
	for id in [&"iron_shard", &"beast_hide", &"stolen_linen", &"arcane_dust", &"wisp_mote"]:
		(parts.get_or_add(id, []) as Array).append("Salvage gear")
	for id in parts:
		_hints[id] = ". ".join((parts[id] as Array).slice(0, 3))
