class_name DungeonGrowth
## Shared dungeon policy. Original floors and flags retain their identities forever.
## A visit snapshots the hero's level in the save; crossing a threshold never changes a loaded run.
const MAX_EXTRA := 6
const STEPS := [25, 35, 45, 50, 55, 60]
const NAMES := ["Deep Galleries", "Buried Crossing", "Forgotten Vaults", "Fractured Halls", "Ancient Treasury", "The Last Depth"]
const REINFORCEMENTS := {
	&"fungal": [&"rootweaver", &"broodhost", &"mire_troll"],
	&"drowned": [&"brinecaller", &"bloodbinder", &"barnacle_hulk"],
	&"ember": [&"ashen_acolyte", &"magma_golem", &"forge_thrall"],
	&"rime": [&"frost_revenant", &"gravecaller", &"barrow_jarl"],
	&"orrery": [&"riftcaller", &"mirror_knight", &"void_seer"],
	&"hideout": [&"bandit_bombardier", &"bandit_marksman", &"ogre_crusher"],
	&"crypt": [&"necromancer", &"gravecaller", &"frost_revenant"],
	&"hive": [&"broodmother", &"broodhost", &"mycelid_hulk"],
	&"mire": [&"plague_bloater", &"bloodbinder", &"mire_troll"],
	&"thorn": [&"rootweaver", &"briar_lasher", &"broodhost"],
	&"sandtomb": [&"mirage_weaver", &"rune_golem", &"shade_stalker"],
	&"storm": [&"storm_herald", &"riftcaller", &"aether_sentinel"],
	&"umbral": [&"shade_stalker", &"bloodbinder", &"void_seer"],
	&"crystal": [&"rune_golem", &"mirror_knight", &"aether_sentinel"],
	&"gilded": [&"treasure_gremlin", &"mirror_knight", &"rune_golem"],
	&"abyss": [&"riftcaller", &"soulbound_twin", &"void_seer"],
	&"cavern": [&"goblin_summoner", &"orc_shaman", &"ogre_crusher"],
}

static func profile(level: int) -> Dictionary:
	level = clampi(level, 1, BH.LEVEL_CAP)
	var extra := 0
	for threshold in STEPS:
		if level >= threshold:
			extra += 1
	var deep := clampf(float(level - 25) / 25.0, 0.0, 1.0)
	var greater := clampf(float(level - 50) / 10.0, 0.0, 1.0)
	return {"level": level, "extra": extra, "stage": 2 if level >= 50 else (1 if level >= 25 else 0),
		"elite_bonus": (0.05 + deep * 0.15 if level >= 25 else 0.0) + (0.12 + greater * 0.08 if level >= 50 else 0.0),
		"pack_bonus": (1 if level >= 35 else 0) + (1 if level >= 50 else 0),
		"reward_bonus": (0.15 + deep * 0.35 if level >= 25 else 0.0) + (0.5 + greater * 0.25 if level >= 50 else 0.0)}

static func visit_key(dungeon: StringName) -> String:
	return "dungeon_visit_level/" + String(dungeon)

static func enter(hero: HeroData, destination: StringName) -> void:
	if hero == null:
		return
	var parsed := DataDungeons.parse(destination)
	if parsed[0] == &"":
		return
	var previous := DataDungeons.parse(hero.current_map)
	var key := visit_key(parsed[0])
	if previous[0] != parsed[0] or not hero.world_flags.has(key):
		hero.world_flags[key] = hero.progress.level
	# When entering an occupied party floor, use its owner's saved visit level.
	if Net.is_active():
		var owner := Net.world_owner(destination)
		if owner != 0 and owner != Net.my_id():
			var peer: Dictionary = Net.peers.get(owner, {})
			hero.world_flags[key] = clampi(int(peer.get("dungeon_level", peer.get("level", hero.progress.level))), 1, BH.LEVEL_CAP)
	# A party portal or saved return point may lead deeper than this hero can open alone.
	# Keep that floor's required stage so it always has a valid exit and consistent geometry.
	var extra_floor := int(parsed[1]) - base_count(parsed[0])
	if extra_floor > 0 and extra_floor <= MAX_EXTRA:
		hero.world_flags[key] = maxi(int(hero.world_flags[key]), STEPS[extra_floor - 1])

static func for_hero(hero: HeroData, dungeon: StringName) -> Dictionary:
	if hero == null:
		return profile(1)
	var level := hero.progress.level
	if DataDungeons.parse(hero.current_map)[0] == dungeon:
		level = int(hero.world_flags.get(visit_key(dungeon), level))
	return profile(level)

static func base_count(dungeon: StringName) -> int:
	return DataDungeons.get_def(dungeon).floors.size()

static func total(hero: HeroData, dungeon: StringName) -> int:
	return base_count(dungeon) + int(for_hero(hero, dungeon).extra)

static func levels(dungeon: StringName, floor_n: int, growth: Dictionary) -> Vector2i:
	var d := DataDungeons.get_def(dungeon)
	var original: Array = d.levels[mini(floor_n, base_count(dungeon)) - 1]
	if int(growth.stage) == 0:
		return Vector2i(original[0], original[1])
	# Ease old dungeons upward from 25 to 35; full matching begins at 35.
	var blend := clampf(float(int(growth.level) - 24) / 11.0, 0.0, 1.0)
	if floor_n > base_count(dungeon):
		blend = 1.0
	var target := int(growth.level) - 3 + mini(floor_n - 1, 5)
	if floor_n > base_count(dungeon):
		target = maxi(int(growth.level), target)
	var lo := maxi(int(original[0]), roundi(lerpf(float(original[0]), float(target), blend)))
	var hi := maxi(int(original[1]), lo + 2)
	return Vector2i(mini(lo, BH.LEVEL_CAP), mini(hi, BH.LEVEL_CAP))

static func pool(dungeon: StringName, original: Array, growth: Dictionary, seed_value: int) -> Array:
	var result := original.duplicate()
	if int(growth.stage) == 0:
		return result
	var theme: StringName = DataDungeons.get_def(dungeon).theme
	var reinforcements: Array = REINFORCEMENTS.get(theme, [&"rune_golem", &"riftcaller", &"void_seer"])
	# Replace actual pack positions: appending to a long pool would never spawn the new enemies.
	var count := 2 if int(growth.stage) == 2 else 1
	for i in count:
		var index := i % maxi(1, result.size())
		var pick := posmod(seed_value + i, reinforcements.size() if int(growth.stage) == 2 else (2 if int(growth.level) >= 35 else 1))
		if result.is_empty():
			result.append(reinforcements[pick])
		else:
			result[index] = reinforcements[pick]
	return result

static func floor_plan(dungeon: StringName, floor_n: int) -> Dictionary:
	var depth := floor_n - base_count(dungeon)
	# Three different routes through a shared, connected gallery footprint. Marker cells stay clear.
	var plan := ["....................", ".000000000000000000.", ".000000000000000000.",
		".000000000000000000.", ".0000~~~00~~~000000.", ".0000~~~00~~~000000.",
		".0000===00===000000.", ".0000~~~00~~~000000.", ".000000000000000000.",
		".000000000000000000.", ".0000~~~00~~~000000.", ".0000~~~00~~~000000.",
		".0000===00===000000.", ".000000000000000000.", ".000000000000000000.", "...................."]
	if depth % 3 == 1:
		plan[6] = ".000000000000000000."
	elif depth % 3 == 2:
		plan[10] = ".000000000000000000."
		plan[11] = ".000000000000000000."
	return {"name": NAMES[clampi(depth - 1, 0, MAX_EXTRA - 1)], "arrival": Vector2i(9, 14),
		"descent": Vector2i(9, 1), "seal": Vector2i(9, 3), "plan": plan,
		"camps": [[Vector2i(3, 10), "a", 4, 0.2], [Vector2i(16, 10), "b", 4, 0.25],
			[Vector2i(3, 5), "b", 4, 0.3], [Vector2i(16, 5), "b", 4, 0.3]],
		"chests": [[Vector2i(2, 2), 1], [Vector2i(17, 2), 2]]}

static func summary(hero: HeroData, dungeon: StringName) -> String:
	return describe(for_hero(hero, dungeon))

static func describe(g: Dictionary) -> String:
	if int(g.stage) == 0:
		return "Deeper floors begin at Level 25; greater changes at Level 50."
	return "%s · %d extra floors · stronger enemies and improved treasure" % [
		"Greater Depths" if int(g.stage) == 2 else "Deep Halls", g.extra]

static func level_notice(level: int, gained: int) -> String:
	var previous := level - gained
	if level >= 50 and previous < 50:
		return "Level 50: greater dungeon depths, larger packs and stronger elites appear on your next visit."
	if level >= 25 and previous < 25:
		return "Level 25: deeper dungeon floors, new enemy groups and class relics appear on your next visit."
	for step in STEPS:
		if previous < step and level >= step:
			return "Another dungeon floor opens on your next visit. Check the entrance or the Dungeon Guide."
	return ""
