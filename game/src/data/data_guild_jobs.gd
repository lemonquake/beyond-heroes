class_name DataGuildJobs
## Miniquest templates of the Guild House (bh-016). Each guild posts its own kind of work on its board:
## the Swordfin Company pays for steel (culling, camps, champions), the Lantern Covenant pays for legwork and care
## (herbs, surveys, crafting, keeping the roads lit).
##
## Template: {id, guild, kind, title, text ({n} = goal, {map} = map name), goal: Vector2i(min, max), unit (gold per unit
## at level 1), lvl: Vector2i(min, max) hero levels the job is posted to, map (kill_map / visit only)}.
## Kinds: kill_any, kill_map, kill_elite, camp, stage, miniboss, herb, craft, visit.

const KINDS := {
	"kill_any": "Slay",
	"kill_map": "Slay",
	"kill_elite": "Elite bounty",
	"camp": "Clear camps",
	"stage": "Clear stages",
	"miniboss": "Champion hunt",
	"herb": "Gather herbs",
	"craft": "Craft",
	"visit": "Survey",
	# bh-030: dynamic postings (made from the world itself, so the board never runs dry)
	"dungeon_kill": "Delve",
	"dungeon_elite": "Dungeon bounty",
	"dungeon_boss": "Lord hunt",
	"dungeon_depth": "Expedition",
	"dungeon_camp": "Purge",
}

## bh-030: kinds whose progress only counts in one place (`map` is a map id, or a dungeon id for the dungeon kinds).
const PLACE_KINDS := ["kill_map", "visit", "dungeon_kill", "dungeon_elite", "dungeon_boss", "dungeon_depth", "dungeon_camp"]
## Hand-written templates whose top level is this or more never age out (the level cap was 60 when they were written;
## it is 300 now).
const OPEN_TOP := 60

## bh-030: dynamic templates. Each is built from a dungeon or a combat map and has the id "dyn:<kind>:<target>".
## {unit at level 1, goal range, title variants, text variants}. {place} = the dungeon or map, {n} = the goal.
const DYNAMIC := {
	"dungeon_kill": {"unit": 9, "goal": Vector2i(25, 45),
		"titles": ["Delve: {place}", "Clear the Halls of {place}", "Deep Work in {place}"],
		"texts": ["The guild wants the halls of {place} thinned before its scouts go in. Slay {n} monsters on any of its floors.",
			"Whatever breeds in {place} spills out onto the roads. Put down {n} of them inside the dungeon.",
			"A purse for every claw: slay {n} monsters anywhere in {place}."]},
	"dungeon_elite": {"unit": 50, "goal": Vector2i(3, 6),
		"titles": ["Wanted in {place}", "Captains of {place}", "Elite Bounty: {place}"],
		"texts": ["The packs of {place} follow their elites. Bring down {n} elite monsters inside it.",
			"Posters name the brutes leading the war bands of {place}. Kill {n} elites there."]},
	"dungeon_boss": {"unit": 420, "goal": Vector2i(1, 1),
		"titles": ["The Lord of {place}", "Unseat the Master of {place}", "A Crown in {place}"],
		"texts": ["Someone rules {place} - its lord, its champion or the usurper who took the sanctum. Defeat {n} of them.",
			"The guild will pay well for proof that the master of {place} has fallen. Defeat its champion, lord or usurper."]},
	"dungeon_depth": {"unit": 70, "goal": Vector2i(2, 4),
		"titles": ["Expedition: {place}", "Map the Depths of {place}", "How Deep Is {place}?"],
		"texts": ["The cartographers need someone on floor {n} of {place}. Reach it (or deeper) and the notes are paid for.",
			"Walk down to floor {n} of {place} and come back to tell of it."]},
	"dungeon_camp": {"unit": 70, "goal": Vector2i(2, 4),
		"titles": ["Purge {place}", "Burn the Nests of {place}", "Break the Camps of {place}"],
		"texts": ["Monster camps keep growing in {place}. Wipe out {n} of them to the last monster.",
			"Clear {n} camps inside {place} so the guild's delvers can pass."]},
	"kill_map": {"unit": 8, "goal": Vector2i(20, 35),
		"titles": ["Patrol: {place}", "Hold {place}", "The Roads of {place}"],
		"texts": ["Travellers keep vanishing in {place}. Cut down {n} monsters there.",
			"The guild's caravans need {place} quiet. Put down {n} monsters on that map."]},
}

const TEMPLATES := [
	# ---- The Swordfin Company: bounties -----------------------------------------------------------------------
	{"id": "sw_westreach", "guild": "swordfin", "kind": "kill_map", "map": "westreach", "title": "Thin the Roadside", "goal": Vector2i(8, 12), "unit": 7, "lvl": Vector2i(1, 8),
		"text": "Goblins keep working the roads below the South Gate. Cut down {n} monsters in {map}."},
	{"id": "sw_forest", "guild": "swordfin", "kind": "kill_map", "map": "ruined_forest", "title": "Fallen Village Patrol", "goal": Vector2i(10, 16), "unit": 8, "lvl": Vector2i(1, 10),
		"text": "The fallen village is never quiet. Put down {n} monsters in the {map}."},
	{"id": "sw_catacombs", "guild": "swordfin", "kind": "kill_map", "map": "catacombs", "title": "Grave Duty", "goal": Vector2i(12, 18), "unit": 10, "lvl": Vector2i(4, 14),
		"text": "The dead keep walking. Put {n} of them back down in the {map}."},
	{"id": "sw_temple", "guild": "swordfin", "kind": "kill_map", "map": "forgotten_temple", "title": "Temple Watch", "goal": Vector2i(12, 18), "unit": 12, "lvl": Vector2i(7, 20),
		"text": "Something old still guards the oath. Cut down {n} of its servants in the {map}."},
	{"id": "sw_cull", "guild": "swordfin", "kind": "kill_any", "title": "General Cull", "goal": Vector2i(20, 30), "unit": 6, "lvl": Vector2i(1, 60),
		"text": "The Commander wants numbers, not stories. Slay {n} monsters, anywhere on Salmonan."},
	{"id": "sw_elite", "guild": "swordfin", "kind": "kill_elite", "title": "Marked Heads", "goal": Vector2i(2, 4), "unit": 45, "lvl": Vector2i(3, 60),
		"text": "Elites lead the packs and the packs do not scatter without them. Bring down {n} elite monsters."},
	{"id": "sw_camp", "guild": "swordfin", "kind": "camp", "title": "Camp Breaker", "goal": Vector2i(1, 3), "unit": 55, "lvl": Vector2i(1, 60),
		"text": "Monster camps grow bolder each week. Wipe out {n} camp(s) to the last monster."},
	{"id": "sw_stage", "guild": "swordfin", "kind": "stage", "title": "Sweep the Field", "goal": Vector2i(1, 2), "unit": 110, "lvl": Vector2i(2, 60),
		"text": "Clear every camp of a combat map in one visit. Do it {n} time(s)."},
	{"id": "sw_champion", "guild": "swordfin", "kind": "miniboss", "title": "Champion Hunt", "goal": Vector2i(1, 1), "unit": 260, "lvl": Vector2i(5, 60),
		"text": "A named champion is worth a purse of its own. Defeat {n} champion."},
	# ---- The Lantern Covenant: errands ------------------------------------------------------------------------
	{"id": "ln_herbs", "guild": "lantern", "kind": "herb", "title": "Herb Run", "goal": Vector2i(5, 8), "unit": 9, "lvl": Vector2i(1, 60),
		"text": "The Archive's dispensary is out of green things. Gather {n} herbs from wild patches."},
	{"id": "ln_survey_forest", "guild": "lantern", "kind": "visit", "map": "ruined_forest", "title": "Field Notes: The Forest", "goal": Vector2i(1, 1), "unit": 70, "lvl": Vector2i(1, 10),
		"text": "Walk the {map} and note what has changed since the last survey. Arrive there to file your notes."},
	{"id": "ln_survey_catacombs", "guild": "lantern", "kind": "visit", "map": "catacombs", "title": "Field Notes: The Deep", "goal": Vector2i(1, 1), "unit": 90, "lvl": Vector2i(4, 16),
		"text": "The Archivist wants eyes on the {map}. Arrive there to file your notes."},
	{"id": "ln_survey_temple", "guild": "lantern", "kind": "visit", "map": "forgotten_temple", "title": "Field Notes: The Oath", "goal": Vector2i(1, 1), "unit": 110, "lvl": Vector2i(7, 24),
		"text": "Verify the wards of the {map}. Arrive there to file your notes."},
	{"id": "ln_survey_olivar", "guild": "lantern", "kind": "visit", "map": "olivar", "title": "Ledger Courier: Olivar", "goal": Vector2i(1, 1), "unit": 60, "lvl": Vector2i(1, 60),
		"text": "Carry the Covenant's ledger copy to {map} by the Lake Shore Road. Arrive there to hand it over."},
	{"id": "ln_survey_wyman", "guild": "lantern", "kind": "visit", "map": "wyman_outpost", "title": "Ledger Courier: Wyman", "goal": Vector2i(1, 1), "unit": 75, "lvl": Vector2i(2, 60),
		"text": "Carry a bundle of registers to {map}. Arrive there to hand it over."},
	{"id": "ln_craft", "guild": "lantern", "kind": "craft", "title": "Steady Hands", "goal": Vector2i(2, 4), "unit": 30, "lvl": Vector2i(2, 60),
		"text": "The Covenant needs supplies made, not bought. Craft {n} item(s) at any forge, alchemy table or workbench."},
	{"id": "ln_specimens", "guild": "lantern", "kind": "kill_any", "title": "Bestiary Specimens", "goal": Vector2i(14, 22), "unit": 7, "lvl": Vector2i(1, 60),
		"text": "The bestiary needs fresh observations. Defeat {n} monsters and note how they fall."},
	{"id": "ln_lights", "guild": "lantern", "kind": "camp", "title": "Keep the Lights Lit", "goal": Vector2i(1, 2), "unit": 60, "lvl": Vector2i(1, 60),
		"text": "Camps snuff the roadside lamps. Clear {n} camp(s) so the lamps can be relit."},
	{"id": "ln_stage", "guild": "lantern", "kind": "stage", "title": "Quiet the Valley", "goal": Vector2i(1, 1), "unit": 120, "lvl": Vector2i(2, 60),
		"text": "Clear every camp of a combat map in one visit so the Covenant's scribes can work in peace."},
	# ---- bh-027: open postings, put up by the guilds that set up in the Guild House ("open": the issuer is one of
	# the hero's rolled guilds, chosen when the job is posted) --------------------------------------------------
	{"id": "op_causeway", "guild": "open", "kind": "kill_map", "map": "weeping_causeway", "title": "Causeway Sweep", "goal": Vector2i(10, 16), "unit": 11, "lvl": Vector2i(5, 24),
		"text": "Travellers vanish on the Weeping Causeway. Cut down {n} monsters in {map} and the guild pays."},
	{"id": "op_west_patrol", "guild": "open", "kind": "kill_map", "map": "westreach", "title": "Westreach Patrol", "goal": Vector2i(14, 20), "unit": 7, "lvl": Vector2i(1, 12),
		"text": "Walk the Westreach roads with a blade out. Put down {n} monsters in {map}."},
	{"id": "op_temple_purge", "guild": "open", "kind": "kill_map", "map": "forgotten_temple", "title": "Purge the Oath", "goal": Vector2i(16, 24), "unit": 12, "lvl": Vector2i(10, 30),
		"text": "The temple's servants still march. Break {n} of them in the {map}."},
	{"id": "op_deep_catacombs", "guild": "open", "kind": "kill_map", "map": "catacombs", "title": "Down Among the Dead", "goal": Vector2i(16, 24), "unit": 10, "lvl": Vector2i(6, 22),
		"text": "Something below the catacombs is waking them. Lay {n} of the dead to rest in the {map}."},
	{"id": "op_heads", "guild": "open", "kind": "kill_elite", "title": "Wanted: Pack Leaders", "goal": Vector2i(3, 5), "unit": 42, "lvl": Vector2i(4, 60),
		"text": "Posters on every door: the leaders of the packs, dead or dead. Bring down {n} elite monsters."},
	{"id": "op_champion", "guild": "open", "kind": "miniboss", "title": "Named and Wanted", "goal": Vector2i(1, 2), "unit": 240, "lvl": Vector2i(8, 60),
		"text": "The guild has a name on the board and a purse beside it. Defeat {n} champion(s)."},
	{"id": "op_camps", "guild": "open", "kind": "camp", "title": "Burn the Camps", "goal": Vector2i(2, 4), "unit": 50, "lvl": Vector2i(1, 60),
		"text": "Monster camps are squatting on good land. Wipe out {n} of them."},
	{"id": "op_stage", "guild": "open", "kind": "stage", "title": "A Quiet Map", "goal": Vector2i(1, 2), "unit": 115, "lvl": Vector2i(3, 60),
		"text": "Clear every camp of a combat map in one visit, {n} time(s). The guild wants the roads safe for its caravans."},
	{"id": "op_herbs", "guild": "open", "kind": "herb", "title": "Healer's Satchel", "goal": Vector2i(6, 10), "unit": 9, "lvl": Vector2i(1, 60),
		"text": "The guild's healers are short of simples. Gather {n} herbs from wild patches."},
	{"id": "op_smith", "guild": "open", "kind": "craft", "title": "Arms for the Recruits", "goal": Vector2i(2, 4), "unit": 32, "lvl": Vector2i(2, 60),
		"text": "New recruits arrive with nothing but hope. Craft {n} item(s) at a forge, alchemy table or workbench."},
	{"id": "op_cull", "guild": "open", "kind": "kill_any", "title": "Thin the Numbers", "goal": Vector2i(25, 40), "unit": 6, "lvl": Vector2i(1, 60),
		"text": "Too many monsters, not enough heroes. Slay {n} of them anywhere on Salmonan."},
	{"id": "op_wyman", "guild": "open", "kind": "visit", "map": "wyman_outpost", "title": "Letters to Wyman", "goal": Vector2i(1, 1), "unit": 80, "lvl": Vector2i(2, 60),
		"text": "A satchel of letters for the soldiers at {map}. Arrive there to deliver them."},
	{"id": "op_olivar", "guild": "open", "kind": "visit", "map": "olivar", "title": "Olivar Market Run", "goal": Vector2i(1, 1), "unit": 60, "lvl": Vector2i(1, 60),
		"text": "The guild's factor in {map} is waiting on a sealed purse. Arrive there to hand it over."},
	{"id": "op_causeway_survey", "guild": "open", "kind": "visit", "map": "weeping_causeway", "title": "Map the Causeway", "goal": Vector2i(1, 1), "unit": 95, "lvl": Vector2i(5, 30),
		"text": "The guild's charts of {map} are years old. Walk it and bring back fresh notes."},
]

static func template(id: String) -> Dictionary:
	if id.begins_with("dyn:"):
		return dynamic_template(id)
	for t in TEMPLATES:
		if String(t.id) == id:
			return t
	return {}

static func for_guild(gid: StringName) -> Array:
	return TEMPLATES.filter(func(t): return String(t.guild) == String(gid))

## bh-027: every posting — the central board of the Guild House offers all of them to everyone.
static func all() -> Array:
	return TEMPLATES

# ---- bh-030: dynamic postings ------------------------------------------------------------------------------------------

## The template for "dyn:<kind>:<target>", or {} when the kind or the place no longer exists.
static func dynamic_template(id: String) -> Dictionary:
	var parts := id.split(":")
	if parts.size() != 3 or not DYNAMIC.has(parts[1]):
		return {}
	var kind := parts[1]
	var target := parts[2]
	var place := ""
	if kind.begins_with("dungeon_"):
		var d := DataDungeons.get_def(StringName(target))
		if d.is_empty():
			return {}
		place = String(d.get("name", target.capitalize()))
	else:
		var md := DB.map_def(StringName(target))
		if md == null:
			return {}
		place = md.display_name
	var spec: Dictionary = DYNAMIC[kind]
	var pick := absi(hash(id))
	var titles: Array = spec.titles
	var texts: Array = spec.texts
	var goal: Vector2i = spec.goal
	if kind == "dungeon_depth":
		var floors := DataDungeons.floor_count(StringName(target))
		goal = Vector2i(clampi(2, 1, floors), maxi(1, floors))
	return {"id": id, "guild": "open", "kind": kind, "map": target, "dynamic": true, "place": place,
		"title": String(titles[pick % titles.size()]).replace("{place}", place),
		"text": String(texts[(pick / 7) % texts.size()]).replace("{place}", place),
		"goal": goal, "unit": int(spec.unit), "lvl": Vector2i(1, BH.LEVEL_CAP)}

## The dungeons a hero can walk into: the gate's map is discovered and the gate's hero-tier lock is met.
static func open_dungeons(hero: HeroData) -> Array:
	var out := []
	if hero == null:
		return out
	for id in DataDungeons.order():
		var d := DataDungeons.get_def(id)
		var surface: StringName = StringName(String((d.get("surface", {}) as Dictionary).get("map", "")))
		if surface != &"" and not hero.discovered_maps.has(surface) and hero.current_map != surface:
			continue
		if hero.tier < DataDungeons.min_tier(id):
			continue
		out.append(id)
	return out

## Every dynamic template open to this hero now: five kinds for each reachable dungeon, a patrol for each discovered
## combat map within reach of the hero's level (DungeonGrowth keeps dungeons level with the hero, so all of them count).
static func dynamic_for(hero: HeroData) -> Array:
	var out := []
	for id in open_dungeons(hero):
		for kind in ["dungeon_kill", "dungeon_elite", "dungeon_boss", "dungeon_depth", "dungeon_camp"]:
			var t := dynamic_template("dyn:%s:%s" % [kind, id])
			if not t.is_empty():
				out.append(t)
	for m in hero.discovered_maps:
		var md := DB.map_def(StringName(m))
		if md == null or md.is_town or md.interior or String(m).begins_with("dg_"):
			continue
		if md.level_max + 25 < hero.progress.level and hero.progress.level < 30:
			continue
		var t2 := dynamic_template("dyn:kill_map:%s" % m)
		if not t2.is_empty():
			out.append(t2)
	return out
