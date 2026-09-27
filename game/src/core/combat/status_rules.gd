class_name StatusRules
## Data for every status effect (debuffs and buffs) and their stacking rules — the one Status Effect Framework table.
##
## Stacking: every status is single-instance per actor. Re-application refreshes the duration to the larger remaining
## value and keeps the stronger magnitude/DoT (never adds a second instance). Statuses listed in STACKING keep a stack
## counter (1..max_stacks) that scales their magnitude; each refresh adds one stack.
## Duration of debuffs is reduced by the target's Status Resistance. Immunities: an actor may be immune to any status id
## (bosses cannot be Frozen or Stunned; they receive Chilled/Staggered instead). Freeze and Stun grant short immunity
## windows after they end so they can never chain-lock a target.

const THRESHOLD := 100.0

# id: {name, debuff, duration, icon, desc, [hidden], [mods: [[stat, op, value]]]}   value scales with magnitude when mag_scaled
const DEFS := {
	&"burning": {"name": "Burning", "debuff": true, "duration": 4.0, "icon": "burning", "desc": "Taking Fire damage over time. Water or Ice extinguishes it; Wind fans it onto nearby enemies."},
	&"chilled": {"name": "Chilled", "debuff": true, "duration": 3.0, "icon": "chilled", "desc": "25% slower movement and attacks. Chill builds toward Freeze."},
	&"frozen": {"name": "Frozen", "debuff": true, "duration": 1.6, "icon": "frozen", "desc": "Cannot act. Heavy physical hits Shatter (+30%); Fire Melts it (+50% Fire)."},
	&"freeze_immune": {"name": "Thawing", "debuff": false, "duration": 4.0, "icon": "", "desc": "Recently frozen; cannot be frozen again yet.", "hidden": true},
	&"shocked": {"name": "Shocked", "debuff": true, "duration": 4.0, "icon": "shocked", "desc": "Takes increased damage from all sources (15%, 25% while Wet)."},
	&"wet": {"name": "Wet", "debuff": true, "duration": 6.0, "icon": "wet", "desc": "Lightning hits harder and Shocks twice as fast, Freeze builds twice as fast, Fire is dampened. Extinguishes Burning."},
	&"cursed": {"name": "Cursed", "debuff": true, "duration": 6.0, "icon": "cursed", "desc": "Takes 15% more damage. Light damage purifies it for a burst."},
	&"purged": {"name": "Purged", "debuff": true, "duration": 5.0, "icon": "purged", "desc": "Regeneration and healing halved, protective wards suppressed. Dark damage rends it (+30%)."},
	&"staggered": {"name": "Staggered", "debuff": true, "duration": 1.1, "icon": "staggered", "desc": "Poise broken; interrupted and unable to act."},
	&"stagger_window": {"name": "Exposed", "debuff": true, "duration": 4.0, "icon": "staggered", "desc": "Takes 30% more damage while recovering from a stagger."},
	&"stunned": {"name": "Stunned", "debuff": true, "duration": 1.2, "icon": "stunned", "desc": "Cannot act."},
	&"stun_immune": {"name": "", "debuff": false, "duration": 3.0, "icon": "", "desc": "", "hidden": true},
	&"bleeding": {"name": "Bleeding", "debuff": true, "duration": 3.0, "icon": "bleeding", "desc": "Taking Physical damage over time."},
	&"poisoned": {"name": "Poisoned", "debuff": true, "duration": 5.0, "icon": "poisoned", "desc": "Taking damage over time and receiving 30% less healing.",
		"mods": [[&"healing", StatModifier.Op.MORE, -0.3]]},
	&"slowed": {"name": "Slowed", "debuff": true, "duration": 3.0, "icon": "slowed", "desc": "30% slower movement.",
		"mods": [[&"move_speed", StatModifier.Op.MORE, -0.3]]},
	&"silenced": {"name": "Silenced", "debuff": true, "duration": 2.5, "icon": "silenced", "desc": "Cannot cast spells. Weapon skills still work."},
	&"weakened": {"name": "Weakened", "debuff": true, "duration": 5.0, "icon": "weakened", "desc": "Deals 20% less damage.",
		"mods": [[&"outgoing_damage", StatModifier.Op.MORE, -0.2]]},
	&"armor_broken": {"name": "Armor Broken", "debuff": true, "duration": 5.0, "icon": "armor_broken", "desc": "40% less Defense. Built up by Earth damage.",
		"mods": [[&"defense", StatModifier.Op.MORE, -0.4]]},
	&"windswept": {"name": "Windswept", "debuff": true, "duration": 2.5, "icon": "windswept", "desc": "15% slower and 30% lower Knockback Resistance. Built up by Wind damage.",
		"mods": [[&"move_speed", StatModifier.Op.MORE, -0.15], [&"knockback_res", StatModifier.Op.FLAT, -0.3]]},
	&"guard": {"name": "Guard", "debuff": false, "duration": 0.0, "icon": "guard", "desc": "Blocking frontal attacks."},
	&"haste": {"name": "Haste", "debuff": false, "duration": 8.0, "icon": "haste", "desc": "15% more movement and attack speed.",
		"mods": [[&"move_speed", StatModifier.Op.MORE, 0.15], [&"attack_speed", StatModifier.Op.MORE, 0.15], [&"cast_speed", StatModifier.Op.MORE, 0.15]]},
	&"regen": {"name": "Regeneration", "debuff": false, "duration": 6.0, "icon": "regen", "desc": "Restoring HP over time."},
	&"shielded": {"name": "Radiant Ward", "debuff": false, "duration": 8.0, "icon": "shielded", "desc": "A barrier absorbs incoming damage."},
	&"empowered": {"name": "Empowered", "debuff": false, "duration": 6.0, "icon": "empowered", "desc": "Deals 20% more damage.",
		"mods": [[&"outgoing_damage", StatModifier.Op.MORE, 0.2]]},
	&"fortified": {"name": "Fortified", "debuff": false, "duration": 6.0, "icon": "fortified", "desc": "Takes 20% less damage.",
		"mods": [[&"damage_taken", StatModifier.Op.MORE, -0.2]]},
	&"war_cry": {"name": "War Cry", "debuff": false, "duration": 10.0, "icon": "valor", "desc": "Increased Defense and Valor generation."},
	&"bulwark": {"name": "Iron Bulwark", "debuff": false, "duration": 6.0, "icon": "guard", "desc": "Increased Block Chance and Knockback Resistance."},
	&"badly_hurt": {"name": "Badly Hurt", "debuff": true, "duration": 0.0, "icon": "badly_hurt", "desc": "Below 30% HP. Your hero is visibly wounded. Drink a potion or break away from the fight."},
	&"resolute": {"name": "Resolute", "debuff": false, "duration": 0.0, "icon": "resolute", "desc": "Valor 50+: 10% more physical damage and knockback."},
	&"overcharged": {"name": "Overcharged", "debuff": false, "duration": 0.0, "icon": "overcharged", "desc": "Maximum Arcane Charge: spells are empowered but you take 15% more damage.",
		"mods": [[&"damage_taken", StatModifier.Op.MORE, 0.15]]},
	&"arcane_amp": {"name": "Arcane Amplification", "debuff": false, "duration": 6.0, "icon": "arcane_charge", "desc": "More spell damage for each different element cast in a row.", "stacks": 5},
	&"overload": {"name": "Elemental Overload", "debuff": false, "duration": 5.0, "icon": "empowered", "desc": "40% more Elemental Damage."},
	&"elite_shield": {"name": "Warded", "debuff": false, "duration": 0.0, "icon": "shielded", "desc": "Elite ward absorbs damage until broken."},
	&"enraged": {"name": "Enraged", "debuff": false, "duration": 0.0, "icon": "empowered", "desc": "Faster and more aggressive."},
	# ---- bh-006 elixirs (consumables); "item" = the base whose rendered icon the buff shows ----
	&"elixir_swift": {"name": "Swiftfoot", "debuff": false, "duration": 60.0, "item": "swiftfoot_tonic", "desc": "20% more Movement Speed.",
		"mods": [[&"move_speed", StatModifier.Op.MORE, 0.2]]},
	&"elixir_ironskin": {"name": "Ironskin", "debuff": false, "duration": 60.0, "item": "ironskin_brew", "desc": "30% more Defense, +10% Knockback Resistance.",
		"mods": [[&"defense", StatModifier.Op.MORE, 0.3], [&"knockback_res", StatModifier.Op.FLAT, 0.1]]},
	&"elixir_berserk": {"name": "Berserk", "debuff": false, "duration": 45.0, "item": "berserker_draught", "desc": "20% more Attack Speed, 10% more damage taken.",
		"mods": [[&"attack_speed", StatModifier.Op.MORE, 0.2], [&"damage_taken", StatModifier.Op.MORE, 0.1]]},
	&"elixir_sage": {"name": "Sage's Focus", "debuff": false, "duration": 60.0, "item": "sages_infusion", "desc": "+25% Magic Damage, 15% more Cast Speed.",
		"mods": [[&"magic_damage", StatModifier.Op.INC, 0.25], [&"cast_speed", StatModifier.Op.MORE, 0.15]]},
	&"elixir_emberward": {"name": "Emberward", "debuff": false, "duration": 120.0, "item": "emberward_potion", "desc": "+25% Fire Resistance.",
		"mods": [[&"res_fire", StatModifier.Op.FLAT, 0.25]]},
	&"elixir_frostward": {"name": "Frostward", "debuff": false, "duration": 120.0, "item": "frostward_potion", "desc": "+25% Ice Resistance.",
		"mods": [[&"res_ice", StatModifier.Op.FLAT, 0.25]]},
	&"elixir_stormward": {"name": "Stormward", "debuff": false, "duration": 120.0, "item": "stormward_potion", "desc": "+25% Lightning Resistance.",
		"mods": [[&"res_lightning", StatModifier.Op.FLAT, 0.25]]},
	&"elixir_fortune": {"name": "Fortune", "debuff": false, "duration": 300.0, "item": "fortune_elixir", "desc": "+30% Magic Find, +25% Gold Find.",
		"mods": [[&"magic_find", StatModifier.Op.FLAT, 0.3], [&"gold_find", StatModifier.Op.FLAT, 0.25]]},
	&"elixir_scholar": {"name": "Scholar's Insight", "debuff": false, "duration": 600.0, "item": "scholars_tea", "desc": "+15% Experience gained.",
		"mods": [[&"xp_gain", StatModifier.Op.FLAT, 0.15]]},
	&"elixir_feather": {"name": "Featherweight", "debuff": false, "duration": 300.0, "item": "featherweight_draught", "desc": "+60 Carry Capacity.",
		"mods": [[&"carry_capacity", StatModifier.Op.FLAT, 60.0]]},
	&"elixir_whetstone": {"name": "Honed Edge", "debuff": false, "duration": 300.0, "item": "whetstone", "desc": "+15% Physical Damage, +10% Critical Damage.",
		"mods": [[&"phys_damage", StatModifier.Op.FLAT, 0.15], [&"crit_damage", StatModifier.Op.FLAT, 0.1]]},
	&"elixir_smoke": {"name": "Smoke Cloud", "debuff": false, "duration": 6.0, "item": "smoke_pellet", "desc": "60% more Evasion, 30% more Movement Speed.",
		"mods": [[&"evasion", StatModifier.Op.MORE, 0.6], [&"move_speed", StatModifier.Op.MORE, 0.3]]},
}

const INTERACTION_DOCS := [
	"**Wet + Lightning** — Conduct: Lightning damage x1.25, Shock buildup x2, Shock strength 25% instead of 15%.",
	"**Wet + Ice** — Freeze buildup x2.",
	"**Burning + Water / Ice** — Extinguish: Burning ends; Water leaves the target Wet.",
	"**Wet + Fire** — Fire damage x0.8 and the Wet status evaporates.",
	"**Fire + Chilled** — Fire thaws: removes Chill and its Freeze buildup.",
	"**Fire + Frozen** — Melt: Fire damage x1.5 and the Freeze ends.",
	"**Frozen + heavy physical / impact** — Shatter: physical damage x1.3, Freeze ends.",
	"**Earth** — builds Armor Break (-40% Defense) and adds up to +50% poise (stagger) damage; heavy impacts on Armor Broken foes stagger harder.",
	"**Wind** — builds Windswept (-30% knockback resistance, slowed); Wind hits fan Burning onto enemies within 4 m.",
	"**Light + Cursed** — Purify: Light damage x1.3 and the Curse is consumed.",
	"**Dark + Purged** — Umbral Rend: Dark damage x1.3 and the Purge is consumed (Light and Dark oppose each other).",
	"**Freeze immunity** — after Freeze ends the target cannot be frozen for 4 s (no permanent freeze-lock).",
	"**Stun immunity** — 3 s after a stun ends.",
]

static func name_of(id: StringName) -> String:
	return DEFS[id]["name"] if DEFS.has(id) else String(id)

static func desc_of(id: StringName) -> String:
	return DEFS[id]["desc"] if DEFS.has(id) else ""

static func icon_of(id: StringName) -> String:
	if DEFS.has(id) and DEFS[id].has("item"):
		return "res://assets/ui/icons/items3d/%s.png" % DEFS[id]["item"]
	var ic: String = DEFS[id].get("icon", "") if DEFS.has(id) else ""
	return "res://assets/ui/icons/status/%s.svg" % ic if ic != "" else ""

static func is_debuff(id: StringName) -> bool:
	return DEFS.has(id) and DEFS[id]["debuff"]

static func is_hidden(id: StringName) -> bool:
	return DEFS.has(id) and DEFS[id].get("hidden", false)

static func base_duration(id: StringName) -> float:
	return DEFS[id]["duration"] if DEFS.has(id) else 3.0

static func max_stacks(id: StringName) -> int:
	return int(DEFS[id].get("stacks", 1)) if DEFS.has(id) else 1

## Default stat modifiers of a status (used when the applier supplies none).
static func default_mods(id: StringName) -> Array:
	var out: Array = []
	if not DEFS.has(id):
		return out
	for m in DEFS[id].get("mods", []):
		out.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, float(m[2]), name_of(id)))
	return out
