class_name DataMinibosses
## Minibosses (bh-007): named champions that hold a camp. Stronger than elites (their own HP/damage multipliers on top
## of the elite ones, larger, fixed modifiers, a HUD bar), each drops Champion Essence, Elite gear and sometimes a
## recipe scroll. Every kill counts as a clear (Olivar's merchants restock). A defeated miniboss returns after RESPAWN
## seconds of play time. Names are provisional (docs/LORE.md §6b); no Filipino words (user rule).
##
## Keys: id, name, title (HUD subtitle), enemy (EnemyDef id), map, pos (map-local x, z), mods (elite modifier ids),
## scale (model/body), hp and damage (MORE multipliers on top of elite scaling), level_bonus, lore.

const RESPAWN := 600.0
const RECIPE_CHANCE := 0.35

const LIST := [
	{"id": &"snagtooth", "name": "Snagtooth the Fence", "title": "Goblin champion", "enemy": &"goblin_skulker", "map": &"westreach",
		"pos": Vector2(-23.5, 47.0), "mods": [&"swift"], "scale": 1.8, "hp": 2.4, "damage": 1.25, "level_bonus": 1,
		"lore": "He sells Lantern Fields' own grain back to Olivar's traders, and keeps the change in a fire-pot."},
	{"id": &"greymaw", "name": "Greymaw", "title": "Pack mother of the coast", "enemy": &"dire_wolf", "map": &"westreach",
		"pos": Vector2(-66.0, 110.0), "mods": [&"berserker"], "scale": 1.45, "hp": 2.2, "damage": 1.2, "level_bonus": 1,
		"lore": "Grey at the muzzle, scarred across the eyes. The fishers leave the clifftop to her after dark."},
	{"id": &"rook", "name": "Rook Hallister", "title": "Smuggler captain", "enemy": &"bandit_cutthroat", "map": &"westreach",
		"pos": Vector2(-185.5, 74.0), "mods": [&"vampiric"], "scale": 1.2, "hp": 2.2, "damage": 1.25, "level_bonus": 2,
		"lore": "The cove's missing shipment passed through his hands, and so did the men who came looking for it."},
	{"id": &"karg", "name": "Warchief Karg", "title": "Orc scout leader", "enemy": &"orc_reaver", "map": &"ruined_forest",
		"pos": Vector2(23.0, 30.0), "mods": [&"armored"], "scale": 1.25, "hp": 2.0, "damage": 1.2, "level_bonus": 1,
		"lore": "Karg's scouts map the Ruined Forest for someone. Nobody knows who pays them."},
	{"id": &"grundle", "name": "Grundle the Chained", "title": "Ogre juggernaut", "enemy": &"ogre_crusher", "map": &"ruined_forest",
		"pos": Vector2(40.0, 25.0), "mods": [&"earthen"], "scale": 1.15, "hp": 1.6, "damage": 1.15, "level_bonus": 1,
		"lore": "Someone chained him to the hillside and left. The chain broke first."},
	{"id": &"ossuary_keeper", "name": "The Ossuary Keeper", "title": "Warden of the bones", "enemy": &"bonewarden", "map": &"catacombs",
		"pos": Vector2(-24.0, -32.0), "mods": [&"shielded", &"cursed"], "scale": 1.3, "hp": 2.0, "damage": 1.2, "level_bonus": 1,
		"lore": "It stacks the dead in careful rows, and adds anyone who interrupts."},
]

## Every champion: the surface ones above and the dungeon champions (DataDungeons, bh-012).
static func all() -> Array:
	return LIST + DataDungeons.minibosses()

static func find(id: StringName) -> Dictionary:
	for m in all():
		if m.id == id:
			return m
	return {}

static func on_map(map_id: StringName) -> Array:
	return all().filter(func(m): return m.map == map_id)

## True while a defeated miniboss is still gone (it returns RESPAWN seconds of play time after its last defeat).
static func resting(hero: HeroData, id: StringName) -> bool:
	if hero == null or not hero.miniboss_log.has(id):
		return false
	return hero.play_time < float(hero.miniboss_log[id].get("at", -INF)) + RESPAWN

static func seconds_until_back(hero: HeroData, id: StringName) -> float:
	if not resting(hero, id):
		return 0.0
	return float(hero.miniboss_log[id].at) + RESPAWN - hero.play_time

## Recipe scrolls a miniboss can drop (those whose source lists minibosses).
static func scroll_pool() -> Array:
	return DataCrafting.SCROLLS.filter(func(s): return String(s[3]).find("minibosses") >= 0).map(func(s): return s[0])

## One line per champion for the rumour-monger: where it holds, and whether it is there now or when it returns.
static func rumours(hero: HeroData) -> String:
	var lines := []
	for m in all():
		var md := DB.map_def(m.map)
		var where := md.display_name if md else String(m.map)
		if resting(hero, m.id):
			lines.append("**%s** (%s): beaten. Back in about %d min." % [m.name, where, ceili(seconds_until_back(hero, m.id) / 60.0)])
		else:
			var kills := int(hero.miniboss_log.get(m.id, {}).get("kills", 0)) if hero else 0
			lines.append("**%s** (%s): %s" % [m.name, where, "waiting for you." if kills == 0 else "back, and angry. Beaten %d time%s." % [kills, "" if kills == 1 else "s"]])
	return "\n".join(lines)
