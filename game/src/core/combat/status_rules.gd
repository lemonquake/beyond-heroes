class_name StatusRules
## Data for every status effect (debuffs and buffs) and their stacking rules.
## Stacking: all statuses are single-instance. Re-application refreshes duration and keeps the stronger magnitude.

const THRESHOLD := 100.0

# id: {name, debuff, duration, icon, desc}
const DEFS := {
	&"burning": {"name": "Burning", "debuff": true, "duration": 4.0, "icon": "burning", "desc": "Taking Fire damage over time."},
	&"chilled": {"name": "Chilled", "debuff": true, "duration": 3.0, "icon": "chilled", "desc": "25% slower movement and attacks. Chill builds toward Freeze."},
	&"frozen": {"name": "Frozen", "debuff": true, "duration": 1.6, "icon": "frozen", "desc": "Cannot act. Heavy physical hits Shatter for 30% more damage."},
	&"freeze_immune": {"name": "Thawing", "debuff": false, "duration": 4.0, "icon": "", "desc": "Recently frozen; cannot be frozen again yet.", "hidden": true},
	&"shocked": {"name": "Shocked", "debuff": true, "duration": 4.0, "icon": "shocked", "desc": "Takes increased damage from all sources."},
	&"wet": {"name": "Wet", "debuff": true, "duration": 6.0, "icon": "wet", "desc": "Lightning hits harder, Freeze builds twice as fast, Fire is dampened. Extinguishes Burning."},
	&"cursed": {"name": "Cursed", "debuff": true, "duration": 6.0, "icon": "cursed", "desc": "Takes 15% more damage. Light damage purifies it for a burst."},
	&"purged": {"name": "Purged", "debuff": true, "duration": 5.0, "icon": "purged", "desc": "Regeneration and protective buffs are suppressed."},
	&"staggered": {"name": "Staggered", "debuff": true, "duration": 1.1, "icon": "staggered", "desc": "Poise broken; interrupted."},
	&"stagger_window": {"name": "Exposed", "debuff": true, "duration": 4.0, "icon": "staggered", "desc": "Takes 30% more damage while recovering from a stagger."},
	&"stunned": {"name": "Stunned", "debuff": true, "duration": 1.2, "icon": "stunned", "desc": "Cannot act."},
	&"stun_immune": {"name": "", "debuff": false, "duration": 3.0, "icon": "", "desc": "", "hidden": true},
	&"bleeding": {"name": "Bleeding", "debuff": true, "duration": 3.0, "icon": "bleeding", "desc": "Taking Physical damage over time."},
	&"guard": {"name": "Guard", "debuff": false, "duration": 0.0, "icon": "guard", "desc": "Blocking frontal attacks."},
	&"haste": {"name": "Haste", "debuff": false, "duration": 8.0, "icon": "haste", "desc": "Faster movement and attacks."},
	&"regen": {"name": "Regeneration", "debuff": false, "duration": 6.0, "icon": "regen", "desc": "Restoring HP over time."},
	&"shielded": {"name": "Radiant Ward", "debuff": false, "duration": 8.0, "icon": "shielded", "desc": "A barrier absorbs incoming damage."},
	&"war_cry": {"name": "War Cry", "debuff": false, "duration": 10.0, "icon": "valor", "desc": "Increased Defense and Valor generation."},
	&"resolute": {"name": "Resolute", "debuff": false, "duration": 0.0, "icon": "valor", "desc": "Valor 50+: 10% more physical damage and knockback."},
	&"overcharged": {"name": "Overcharged", "debuff": false, "duration": 0.0, "icon": "arcane_charge", "desc": "Maximum Arcane Charge: spells are empowered but you take 15% more damage."},
	&"elite_shield": {"name": "Warded", "debuff": false, "duration": 0.0, "icon": "shielded", "desc": "Elite ward absorbs damage until broken."},
}

const INTERACTION_DOCS := [
	"**Wet + Lightning** — Lightning damage x1.25, Shock buildup x2, Shock strength 25% instead of 15%.",
	"**Wet + Ice** — Freeze buildup x2.",
	"**Burning + Water** — Water extinguishes Burning and leaves the target Wet.",
	"**Wet + Fire** — Fire damage x0.8 and the Wet status evaporates.",
	"**Fire vs Chilled/Frozen** — Fire thaws: removes Chill and Freeze buildup.",
	"**Frozen + heavy physical / impact** — Shatter: physical damage x1.3, Freeze ends.",
	"**Earth + strong physical impact** — Earth share adds up to +50% poise (stagger) damage.",
	"**Wind + Burning** — Wind hits fan Burning onto enemies within 4 m.",
	"**Light + Cursed** — Purify: light damage x1.3 and the Curse is consumed.",
	"**Freeze immunity** — after Freeze ends the target cannot be frozen for 4 s (no permanent freeze-lock).",
	"**Stun immunity** — 3 s after a stun ends.",
]

static func name_of(id: StringName) -> String:
	return DEFS[id]["name"] if DEFS.has(id) else String(id)

static func is_debuff(id: StringName) -> bool:
	return DEFS.has(id) and DEFS[id]["debuff"]

static func is_hidden(id: StringName) -> bool:
	return DEFS.has(id) and DEFS[id].get("hidden", false)

static func base_duration(id: StringName) -> float:
	return DEFS[id]["duration"] if DEFS.has(id) else 3.0
