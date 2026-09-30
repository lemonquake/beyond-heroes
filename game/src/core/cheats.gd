class_name Cheats
## Cheat codes typed into the chat box (ChatBox). Codes are case-insensitive and must be the whole message.
##   lemonq  +5000 gold
##   taicho  +1000 gold
##   greg    +1000 gold
##   azrin   +3 levels (levels, points and all, exactly as if earned)
##   azrael  full HP and mana (the hero and every living Tempo at their side)
##   alj    Aljay's Ember Dragon set (sword, shield, cuirass) as Unbound copies: no level or attribute requirement,
##          wearable from Class E, four sockets open; knights only (DataSpecialWeapons)
##   quake team  calls an AI ally hero to fight beside you (up to 3, Single Player only): it follows, protects, shops for the
##               best gear, binds a Tempo and heals itself (QuakeTeam)

const GOLD := 5000
const SMALL_GOLD := 1000
const LEVELS := 3
const CODES := {"lemonq": "gold", "taicho": "small_gold", "greg": "small_gold", "azrin": "levels", "azrael": "restore", "quake team": "quake_team",
	"asdf": "large_gold", "lol": "skill_points", "jjwp": "stat_points",
	"deep pockets": "rich", "talenttime": "talent_points", "oneup": "one_level", "redbottle": "health_items",
	"bluebottle": "mana_items", "homeward": "portal_items", "embers": "ember_items", "wellrested": "rest",
	"freshstart": "reset_stats", "secondwind": "revive_tempos", "alj": "special_weapons"}

## Player-facing reference, also used by tools/create_cheats_pdf.py. Keep one entry for every code.
const DESCRIPTIONS := {
	"lemonq": "Add 5,000 gold.",
	"taicho": "Add 1,000 gold.",
	"greg": "Add 1,000 gold.",
	"azrin": "Gain 3 levels and their normal stat, skill and talent points; stops at the level cap.",
	"azrael": "Fully restore HP and mana for your living hero and living active Tempos. Does not revive the hero.",
	"quake team": "Call one AI ally, up to three allies. Single Player only.",
	"asdf": "Add 50,000 gold.",
	"lol": "Add 10 unspent skill points.",
	"jjwp": "Add 20 unspent stat points.",
	"deep pockets": "Add 100,000 gold.",
	"talenttime": "Add 10 unspent talent points.",
	"oneup": "Gain 1 level and its normal points; stops at the level cap.",
	"redbottle": "Add 20 Health Draughts. Requires enough bag or belt space for the entire gift.",
	"bluebottle": "Add 20 Mana Draughts. Requires enough bag or belt space for the entire gift.",
	"homeward": "Add 10 Town Portal Scrolls. Requires enough bag or belt space for the entire gift.",
	"embers": "Add 100 Soul Embers for Tempo summoning. Requires enough bag space for the entire gift.",
	"wellrested": "Grant at least 30 minutes of Well Rested: +10% XP and +0.5 HP regeneration. Uses play time.",
	"freshstart": "Refund all allocated stat points for free. Does not reset your level, skills or talents.",
	"secondwind": "Revive all fallen bound Tempos at full HP and mana for free. Does not revive the hero.",
	"alj": "Add Aljay's Ember Dragon set (Ember Dragonslayer, Aegis of Fragnir, Ember Dragonhide) as Unbound Legendary copies with 4 sockets: no level or attribute requirements, wearable from Class E. Knights only (and Swordsman and Warden Tempos). Requires enough bag space for all three."
}

static func is_code(text: String) -> bool:
	return CODES.has(text.strip_edges().to_lower())

## Applies `text` if it is a cheat code. Returns the line to show in the chat, or "" when `text` is not a code.
static func apply(text: String, hero: HeroData, player: Node = null) -> String:
	if not is_code(text):
		return ""
	if hero == null:
		return "No hero to apply this cheat to."
	match String(CODES.get(text.strip_edges().to_lower(), "")):
		"large_gold":
			return _give_gold(hero, 50000)
		"rich":
			return _give_gold(hero, 100000)
		"skill_points":
			hero.progress.skill_points += 10
			hero.progress.points_changed.emit()
			return "Cheat: +10 skill points."
		"stat_points":
			hero.progress.free_points += 20
			hero.progress.points_changed.emit()
			return "Cheat: +20 stat points."
		"talent_points":
			hero.progress.talent_points += 10
			hero.progress.points_changed.emit()
			return "Cheat: +10 talent points."
		"one_level":
			return _give_levels(hero, 1)
		"health_items":
			return _give_items(hero, &"health_potion", 20)
		"mana_items":
			return _give_items(hero, &"mana_potion", 20)
		"portal_items":
			return _give_items(hero, &"town_portal", 10)
		"ember_items":
			return _give_items(hero, TempoGacha.EMBER, 100)
		"rest":
			hero.rested_until = maxf(hero.rested_until, hero.play_time + 1800.0)
			hero.stats_dirty.emit()
			return "Cheat: Well Rested for at least 30 minutes of play time."
		"reset_stats":
			hero.progress.reset_attributes()
			return "Cheat: allocated stat points refunded."
		"revive_tempos":
			var restored := 0
			for t in hero.tempos:
				if t.fallen:
					# A just-fallen actor can still be fading out. Remove it before spawning
					# the replacement so actor_for() cannot suppress the revived spirit.
					for actor in TempoParty.actors():
						if actor is Tempo and actor.hero == hero and actor.data == t and not actor.alive:
							actor.queue_free()
					t.fallen = false
					t.hp_frac = 1.0
					t.mana_frac = 1.0
					restored += 1
			if restored > 0:
				if hero == Game.hero:
					TempoParty.refresh(hero)
				Events.tempo_changed.emit(0)
			return "Cheat: %d fallen Tempos revived." % restored
		"gold":
			return _give_gold(hero, GOLD)
		"small_gold":
			return _give_gold(hero, SMALL_GOLD)
		"levels":
			return _give_levels(hero, LEVELS)
		"quake_team":
			var r := QuakeTeam.summon(hero, player as Node3D)
			return ("Cheat: " if r.ok else "") + String(r.text)
		"special_weapons":
			return _give_special(hero)
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

static func _give_levels(hero: HeroData, count: int) -> String:
	var pr := hero.progress
	if pr.level >= BH.LEVEL_CAP:
		return "Cheat: already at the level cap (%d)." % BH.LEVEL_CAP
	var want := mini(pr.level + count, BH.LEVEL_CAP)
	var from := pr.level
	pr.add_xp(XpCurve.total_xp_for_level(want) - XpCurve.total_xp_for_level(pr.level) - pr.xp)
	return "Cheat: level %d -> %d." % [from, pr.level]

static func _give_items(hero: HeroData, base_id: StringName, count: int) -> String:
	var item := DB.make_item(base_id, BH.Rarity.COMMON, 1, 1)
	if item == null:
		return "Cheat: item is unavailable."
	item.count = count
	if not hero.inventory.can_fit(item):
		return "Cheat: make room in your bag or belt for %d %s; nothing added." % [count, item.base.display_name]
	hero.inventory.add(item)
	return "Cheat: +%d %s." % [count, item.base.display_name]

## bh-024/026 "alj": Aljay's Ember Dragon set (DataSpecialWeapons) as Unbound copies with four open sockets.
static func _give_special(hero: HeroData) -> String:
	var ids := DataSpecialWeapons.ids()
	if ids.is_empty():
		return "Cheat: no special equipment is in this build."
	if hero.inventory.free_cells() < ids.size():
		return "Cheat: make room in your bag for %d pieces; nothing added." % ids.size()
	var names: Array[String] = []
	var first: ItemInstance = null
	for id in ids:
		var it := DataSpecialWeapons.unbound(id, hero.progress.level)
		if it:
			hero.inventory.add(it)
			names.append(it.display_name())
			first = it if first == null else first
	var note := "Unbound, %d sockets, wearable from Class %s" % [DataSpecialWeapons.UNBOUND_SOCKETS, DataGuilds.letter(DataSpecialWeapons.UNBOUND_RANK)]
	if first and hero.cls and not DataSpecialWeapons.can_wear(first.base, hero.cls.id):
		note += "; %s" % DataSpecialWeapons.wearers_text(first.base)
	elif hero.tier < DataSpecialWeapons.UNBOUND_RANK:
		note += "; register with a guild to wear them"
	return "Cheat: +%s (%s)." % [", ".join(names), note]

static func _give_gold(hero: HeroData, amount: int) -> String:
	if hero == null:
		return "No hero to give gold to."
	hero.inventory.gold += amount
	hero.inventory.changed.emit()
	Audio.play_ui(&"gold_pickup")
	return "Cheat: +%d gold (now %d)." % [amount, hero.inventory.gold]
