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
]

static func template(id: String) -> Dictionary:
	for t in TEMPLATES:
		if String(t.id) == id:
			return t
	return {}

static func for_guild(gid: StringName) -> Array:
	return TEMPLATES.filter(func(t): return String(t.guild) == String(gid))
