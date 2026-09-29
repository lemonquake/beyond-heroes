class_name Cheats
## Cheat codes typed into the chat box (ChatBox). Codes are case-insensitive and must be the whole message.
##   lemonq  +5000 gold
##   taicho  +1000 gold
##   greg    +1000 gold
##   azrin   +3 levels (levels, points and all, exactly as if earned)
##   azrael  full HP and mana (the hero and every living Tempo at their side)
##   quake team  calls an AI ally hero to fight beside you (up to 3, Single Player only): it follows, protects, shops for the
##               best gear, binds a Tempo and heals itself (QuakeTeam)

const GOLD := 5000
const SMALL_GOLD := 1000
const LEVELS := 3
const CODES := {"lemonq": "gold", "taicho": "small_gold", "greg": "small_gold", "azrin": "levels", "azrael": "restore", "quake team": "quake_team"}

static func is_code(text: String) -> bool:
	return CODES.has(text.strip_edges().to_lower())

## Applies `text` if it is a cheat code. Returns the line to show in the chat, or "" when `text` is not a code.
static func apply(text: String, hero: HeroData, player: Node = null) -> String:
	match String(CODES.get(text.strip_edges().to_lower(), "")):
		"gold":
			return _give_gold(hero, GOLD)
		"small_gold":
			return _give_gold(hero, SMALL_GOLD)
		"levels":
			if hero == null:
				return "No hero to level up."
			var pr := hero.progress
			if pr.level >= BH.LEVEL_CAP:
				return "Cheat: already at the level cap (%d)." % BH.LEVEL_CAP
			var want := mini(pr.level + LEVELS, BH.LEVEL_CAP)
			var from := pr.level
			pr.add_xp(XpCurve.total_xp_for_level(want) - XpCurve.total_xp_for_level(pr.level) - pr.xp)
			return "Cheat: level %d -> %d." % [from, pr.level]
		"quake_team":
			var r := QuakeTeam.summon(hero, player as Node3D)
			return ("Cheat: " if r.ok else "") + String(r.text)
		"restore":
			var pl := player as Player
			if pl == null or not pl.alive:
				return "Cheat: nothing to restore (the hero is not standing)."
			NpcServices.heal(pl)
			for t in TempoParty.actors(pl.get_tree()):
				var a := t as Actor
				if a and a.alive:
					a.heal(a.max_hp() - a.hp, false)
					a.restore_mana(a.max_mana())
			return "Cheat: HP and mana fully restored."
	return ""

static func _give_gold(hero: HeroData, amount: int) -> String:
	if hero == null:
		return "No hero to give gold to."
	hero.inventory.gold += amount
	hero.inventory.changed.emit()
	Audio.play_ui(&"gold_pickup")
	return "Cheat: +%d gold (now %d)." % [amount, hero.inventory.gold]
