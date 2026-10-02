extends Node
## bh-033 loot pool audit: resolves every reachable monster's material pool with the game's own LootPools, validates
## the pool data, and checks every crafting, enchanting and tempering ingredient against its reachable sources.
##   godot --headless --path game res://tests/tools/loot_pool_audit.tscn -- --out=<dir>
## Writes <dir>/loot_audit.json and <dir>/loot_audit.md. Builds every overworld map once (no saves: slot 97).

var out_dir := "user://loot_audit"
var sources := {}        # item -> [{where, enemy, level, per_kill}]
var reach := {}          # enemy id -> [{where, level, kills_per_clear, ctx}]
var herbs := {}          # item -> [{where, patches}]
var errors := []
var unresolved := []

func _ready() -> void:
	Game.save_slot = 97
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	DirAccess.make_dir_recursive_absolute(out_dir)
	Game.hero = Game.new_hero(&"knight", "Loot audit")
	_validate()
	await _overworld()
	_dungeons()
	var report := {"errors": errors, "unresolved": unresolved, "coverage": _coverage(), "routes": _routes(), "first_craft": _first_craft()}
	var f := FileAccess.open(out_dir.path_join("loot_audit.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	var md := FileAccess.open(out_dir.path_join("loot_audit.md"), FileAccess.WRITE)
	md.store_string(_markdown(report))
	md.close()
	print("LOOT_AUDIT errors=%d unresolved=%d written to %s" % [errors.size(), unresolved.size(), out_dir])
	get_tree().quit()

func _check_entry(e: Array, where: String) -> void:
	if DB.item_base(StringName(e[0])) == null and e[0] != &"signature":
		errors.append("%s: unknown item %s" % [where, e[0]])
	if e.size() >= 4 and (float(e[1]) <= 0.0 or float(e[1]) > 1.0 or int(e[2]) < 1 or int(e[3]) < int(e[2])):
		errors.append("%s: bad chance/count %s" % [where, str(e)])

func _validate() -> void:
	var families := {}
	for def: EnemyDef in DB.enemies.values():
		families[def.family] = true
		for e in def.loot:
			_check_entry(e, "enemy %s" % def.id)
	for fam in DataLootPools.FAMILY:
		if not families.has(fam):
			errors.append("FAMILY %s matches no enemy" % fam)
		for e in DataLootPools.FAMILY[fam]:
			_check_entry(e, "family %s" % fam)
	var themes := {}
	for dg in DataDungeons.order():
		themes[StringName(DataDungeons.get_def(dg).get("theme", ""))] = true
		if DB.item_base(StringName(DataDungeons.get_def(dg).get("material", ""))) == null:
			errors.append("dungeon %s: signature material missing" % dg)
	for t in themes:
		if not DataLootPools.THEME.has(t):
			errors.append("theme %s has no THEME pool (inherits nothing)" % t)
	for t in DataLootPools.THEME:
		if not themes.has(t):
			errors.append("THEME %s matches no dungeon" % t)
		for e in DataLootPools.THEME[t]:
			_check_entry(e, "theme %s" % t)
	for dg in DataLootPools.DUNGEON:
		if DataDungeons.get_def(dg).is_empty():
			errors.append("DUNGEON %s is not a dungeon" % dg)
		for e in DataLootPools.DUNGEON[dg].get("add", []):
			_check_entry(e, "dungeon %s" % dg)
	for m in DataLootPools.MAP:
		if DB.map_def(m) == null:
			errors.append("MAP %s is not a map" % m)
	for rows in [DataLootPools.BOSS_COMPLETION, DataLootPools.USURPER_COMPLETION] + DataLootPools.CHEST_SUPPLY:
		for e in rows:
			_check_entry([e[0], 0.5, e[1], e[2]], "completion")

func _add_reach(eid: StringName, where: String, level: int, kills: float, ctx: Dictionary) -> void:
	(reach.get_or_add(eid, []) as Array).append({"where": where, "level": level, "kills": kills, "ctx": ctx})

func _overworld() -> void:
	var ids := DB.maps.keys()
	ids.sort()
	for id in ids:
		var def: MapDef = DB.maps[id]
		if def.interior or String(id).begins_with("dg_"):
			continue
		var m := Game.build_map(id)
		if m == null:
			continue
		add_child(m)
		await get_tree().process_frame
		var ctx := LootPools.context_for_map(id)
		for z in get_tree().get_nodes_in_group(&"enemy_zone"):
			if not m.is_ancestor_of(z):
				continue
			var ens: Array = z.get_meta(&"enemies", [])
			var count := int(z.get_meta(&"count", 3))
			var lv := def.level_min
			if z.has_meta(&"levels"):
				lv = (z.get_meta(&"levels") as Vector2i).x
			for i in count:
				if not ens.is_empty():
					_add_reach(StringName(ens[i % ens.size()]), String(id), lv, 1.0, ctx)
		for g in m.find_children("*", "GatherNode", true, false):
			var h: StringName = (g as GatherNode).herb
			(herbs.get_or_add(h, []) as Array).append({"where": String(id), "level": def.level_min})
		for mb in DataMinibosses.on_map(id):
			_add_reach(StringName(mb.enemy), String(id) + " (champion)", def.level_max, 0.0, ctx)
		m.queue_free()
		await get_tree().process_frame

func _dungeons() -> void:
	for dg in DataDungeons.order():
		var d := DataDungeons.get_def(dg)
		var pools: Dictionary = d.get("pools", {})
		var floors: Array = d.get("levels", [])
		for fi in floors.size():
			var ctx := LootPools.context_for_map(DataDungeons.map_id(dg, fi + 1))
			var camps := 5
			var fd := DataDungeons.floor_def(dg, fi + 1)
			if not fd.is_empty():
				camps = (fd.get("camps", []) as Array).size()
			for key in ["a", "b"]:
				var lst: Array = pools.get(key, [])
				for e in lst:
					_add_reach(StringName(e), "%s floor %d" % [dg, fi + 1], int(floors[fi][0]), float(camps) * 4.0 / maxf(1.0, lst.size() * 2.0), ctx)

func _coverage() -> Array:
	# supply: per item, every reachable monster's resolved entries
	for eid in reach:
		var def := DB.enemy(eid)
		if def == null:
			errors.append("spawned enemy %s has no definition" % eid)
			continue
		for r in reach[eid]:
			var entries := LootPools.resolve(def, r.ctx)
			if entries.is_empty() and not unresolved.has(String(eid)):
				unresolved.append(String(eid))
			for e in entries:
				var per := float(e.chance) * (float(e.min) + float(e.max)) * 0.5
				(sources.get_or_add(e.id, []) as Array).append({"where": r.where, "enemy": String(eid), "level": r.level, "per_kill": per, "layer": e.layer})
	# demand: recipes, enchant ranks, fore-tech ranks
	var demand := {}
	for r in DataCrafting.all():
		for inp in r.inputs:
			(demand.get_or_add(inp[0], []) as Array).append({"use": "recipe %s" % r.id, "level": int(r.get("level", 1)), "count": int(inp[1])})
	for en in DataUpgrades.ENCHANTS:
		for rank in range(1, DataUpgrades.ENCHANT_MAX + 1):
			var c := DataUpgrades.enchant_cost(en, rank)
			for inp in c.inputs:
				(demand.get_or_add(inp[0], []) as Array).append({"use": "enchant %s %d" % [en, rank], "level": int(c.level), "count": int(inp[1])})
	for rank in range(1, DataUpgrades.TECH_MAX + 1):
		var c2 := DataUpgrades.tech_cost(rank)
		for inp in c2.inputs:
			(demand.get_or_add(inp[0], []) as Array).append({"use": "fore-tech %d" % rank, "level": int(c2.level), "count": int(inp[1])})
	var crafted := {}
	for r in DataCrafting.all():
		if (r.out as Dictionary).has("base"):
			crafted[StringName(r.out.base)] = r
	var rows := []
	for id in demand:
		var uses: Array = demand[id]
		var first_use := 999
		for u in uses:
			first_use = mini(first_use, int(u.level))
		var src: Array = sources.get(id, [])
		var earliest := 999
		var best := 0.0
		var places := {}
		for s in src:
			if float(s.per_kill) > 0.0:
				earliest = mini(earliest, int(s.level))
				best = maxf(best, float(s.per_kill))
				places[s.where] = true
		var other := []
		if herbs.has(id):
			other.append("herb patches (%d)" % (herbs[id] as Array).size())
			earliest = mini(earliest, int((herbs[id] as Array).map(func(h): return h.level).min()))
		if crafted.has(id):
			other.append("crafted: %s" % crafted[id].name)
			earliest = mini(earliest, int(crafted[id].get("level", 1)))
		if id == &"champion_essence":
			other.append("every champion")
		var flags := []
		if src.is_empty() and other.is_empty():
			flags.append("NO SOURCE")
		elif earliest > first_use + 5:
			flags.append("first source L%d after first use L%d" % [earliest, first_use])
		if not src.is_empty() and best < 0.05 and other.is_empty():
			flags.append("thin supply")
		var b := DB.item_base(id)
		rows.append({"item": String(id), "name": b.display_name if b else String(id), "first_use_level": first_use, "uses": uses.size(),
			"earliest_source_level": earliest if earliest < 999 else -1, "monster_places": places.size(), "best_per_kill": snappedf(best, 0.001),
			"other": other, "hint": LootPools.source_hint(id), "flags": flags})
	rows.sort_custom(func(a, b): return a.first_use_level < b.first_use_level or (a.first_use_level == b.first_use_level and a.item < b.item))
	return rows

## Units per full clear of representative early routes (every camp once), from the resolved pools.
func _routes() -> Array:
	var out := []
	for where in ["westreach", "ruined_forest", "catacombs", "warren floor 1", "cellars floor 1", "deeps floor 1"]:
		var totals := {}
		var monster_only := {}
		var kills := 0.0
		for eid in reach:
			for r in reach[eid]:
				if r.where != where:
					continue
				kills += float(r.kills)
				for e in LootPools.resolve(DB.enemy(eid), r.ctx):
					var u := float(r.kills) * float(e.chance) * (float(e.min) + float(e.max)) * 0.5
					totals[String(e.id)] = float(totals.get(String(e.id), 0.0)) + u
					if e.layer == "monster":
						monster_only[String(e.id)] = float(monster_only.get(String(e.id), 0.0)) + u
		for k in totals:
			totals[k] = snappedf(totals[k], 0.1)
		for k in monster_only:
			monster_only[k] = snappedf(monster_only[k], 0.1)
		out.append({"route": where, "kills": snappedf(kills, 0.1), "units": totals, "monster_table_only": monster_only})
	return out

## Expected kills (no pity) on the opening route to afford the first forge recipes.
func _first_craft() -> Array:
	var wr: Dictionary = {}
	for r in _routes():
		if r.route == "westreach":
			wr = r
	var out := []
	var kills := float(wr.get("kills", 1.0))
	for spec in [["Steel Ingot", {"iron_shard": 5}], ["Tempered Weapon", {"iron_shard": 10, "beast_hide": 2, "wolf_fang": 2}],
			["Tempered Armor", {"iron_shard": 5, "beast_hide": 6}], ["Hunter's Charm", {"wolf_fang": 3, "beast_hide": 2, "iron_shard": 2}],
			["Fore-Tech rank 1", {"iron_shard": 9}]]:
		var worst := 0.0
		var limiting := ""
		for item in spec[1]:
			var per_clear := float((wr.get("units", {}) as Dictionary).get(item, 0.0))
			var clears := INF if per_clear <= 0.0 else float(spec[1][item]) / per_clear
			if clears > worst:
				worst = clears
				limiting = item
		out.append({"goal": spec[0], "westreach_clears": snappedf(worst, 0.1) if worst < INF else -1, "kills": roundi(worst * kills) if worst < INF else -1, "limited_by": limiting})
	return out

func _markdown(r: Dictionary) -> String:
	var s := "# Loot pool audit\n\nResolved with LootPools (monster > family > dungeon theme/signature/own > region). Herb patches and crafted stock listed separately.\n\n"
	s += "## Validation\n\n%s\n\nMonsters reached with no material entry (documented: they drop gold, gear and potions only): %s\n\n" % [
		"No errors." if r.errors.is_empty() else "\n".join(r.errors.map(func(e): return "- " + e)), ", ".join(r.unresolved) if not r.unresolved.is_empty() else "none"]
	s += "## Ingredient coverage\n\n| Ingredient | First use (level) | Uses | Earliest source (level) | Monster places | Best per kill | Other sources | Hint shown | Flags |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
	for c in r.coverage:
		s += "| %s | %d | %d | %s | %d | %s | %s | %s | %s |\n" % [c.name, c.first_use_level, c.uses, str(c.earliest_source_level), c.monster_places, c.best_per_kill,
			", ".join(c.other), c.hint, ", ".join(c.flags) if not c.flags.is_empty() else "ok"]
	s += "\n## Units per full clear (expected, every camp once)\n\n"
	for rt in r.routes:
		var parts := []
		var keys: Array = rt.units.keys()
		keys.sort()
		for k in keys:
			parts.append("%s %s" % [k, rt.units[k]])
		s += "- **%s** (%s kills): %s\n  - Iron Shard from monster tables alone (before bh-033): %s; with family and place layers: %s\n" % [
			rt.route, rt.kills, ", ".join(parts), rt.monster_table_only.get("iron_shard", 0.0), rt.units.get("iron_shard", 0.0)]
	s += "\n## Time to first craft on the opening route (Westreach, no bad-luck protection)\n\n| Goal | Clears | Kills | Limited by |\n| --- | --- | --- | --- |\n"
	for fc in r.first_craft:
		s += "| %s | %s | %s | %s |\n" % [fc.goal, fc.westreach_clears, fc.kills, fc.limited_by]
	return s
