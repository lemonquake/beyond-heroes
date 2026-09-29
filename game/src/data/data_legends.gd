class_name DataLegends
## bh-021: the legends of the main story — the Dawnbreakers (Class SX) and the Chain-Marshal who betrayed them to the
## Forsaken Legion. Names are the author's (Aljay, Roydo, Paul David); epithets, levels and colours are this build's.
## Class SX ("Beyond") is not a guild tier a hero can reach: it is shown only on these names, with its own emblem.

const SX_EMBLEM := "res://assets/ui/tiers/tier_sx.svg"
const SX_TITLE := "Beyond"

## style -> colours: a (bright), b (deep), hi (highlight), glow (plate / aura)
const STYLES := {
	&"wrath": {"a": Color(1.0, 0.16, 0.08), "b": Color(0.28, 0.0, 0.03), "hi": Color(1.0, 0.82, 0.62), "glow": Color(1.0, 0.1, 0.05),
		"ember": Color(1.0, 0.25, 0.08)},
	&"holy": {"a": Color(1.0, 0.86, 0.45), "b": Color(0.62, 0.36, 0.08), "hi": Color(1.0, 1.0, 0.92), "glow": Color(1.0, 0.8, 0.4),
		"ember": Color(1.0, 0.85, 0.5)},
	&"storm": {"a": Color(0.55, 0.85, 1.0), "b": Color(0.1, 0.22, 0.55), "hi": Color(0.95, 0.98, 1.0), "glow": Color(0.4, 0.75, 1.0),
		"ember": Color(0.6, 0.85, 1.0)},
	&"forsaken": {"a": Color(0.72, 0.5, 1.0), "b": Color(0.12, 0.04, 0.22), "hi": Color(0.95, 0.85, 1.0), "glow": Color(0.6, 0.3, 1.0),
		"ember": Color(0.65, 0.35, 1.0)},
}

const LEGENDS := {
	&"aljay": {"name": "Aljay", "epithet": "The Forsaken Hero", "rank": "SX", "level": 287, "style": &"wrath",
		"model": "aljay", "scale": 1.14, "weapon": "dusk_piercer",
		"line": "Consumed by the Dusk Tyrant's wrath. His heart never faltered."},
	&"roydo": {"name": "Roydo", "epithet": "The Righteous Hammer", "rank": "SX", "level": 264, "style": &"holy",
		"model": "roydo", "scale": 1.17, "weapon": "dawnmaul",
		"line": "There was never a wall in Jre he could not become."},
	&"paul_david": {"name": "Paul David", "epithet": "The Tempest Blade", "rank": "SX", "level": 251, "style": &"storm",
		"model": "paul_david", "scale": 1.03, "weapon": "stormwake",
		"line": "The last of the Dawnbreakers who can still be found."},
	&"kethrax": {"name": "Kethrax", "epithet": "Chain-Marshal of the Forsaken", "rank": "", "level": 0, "style": &"forsaken",
		"model": "kethrax", "scale": 1.28, "weapon": "kethrax_mace",
		"line": "He took Aljay in chains three winters ago."},
}

static func legend(id: StringName) -> Dictionary:
	return LEGENDS.get(id, {})

static func style(id: StringName) -> Dictionary:
	return STYLES.get(id, STYLES[&"holy"])

## "Class SX · Lv 287" (empty rank: the level only, or nothing).
static func rank_line(id: StringName) -> String:
	var l := legend(id)
	if l.is_empty():
		return ""
	var parts: Array = []
	if String(l.rank) != "":
		parts.append("Class %s" % l.rank)
	if int(l.level) > 0:
		parts.append("Lv %d" % int(l.level))
	return " · ".join(parts)
