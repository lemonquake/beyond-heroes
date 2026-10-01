class_name DataEnemiesSpecial
## bh-028: the lords of the five special dungeons (DataDungeonsSpecial). Each is an existing boss re-cast: its attacks,
## phases and model, a new name, tint, size and lore, and more health and damage. No code reads a boss by id, so a
## copy behaves exactly like its template.

const HP := 1.6
const DAMAGE := 1.25

## [new id, template boss, name, tint, model scale x, lore]
const LORDS := [
	[&"seraphel", &"prism_colossus", "Seraphel, the Prismheart", Color(0.85, 0.95, 1.0), 1.15,
		"The crystal at the heart of the Hollows woke when the sky cracked. It remembers being a star, and it would like to be one again."],
	[&"morrowgaunt", &"hollow_dark", "Morrowgaunt, King Below", Color(0.45, 0.95, 0.9), 1.15,
		"The first of the drowned to reach the bottom of the river. He built a throne from the ferry and has been waiting for company."],
	[&"zephyrion", &"voltaric", "Zephyrion, the Aether Heart", Color(0.78, 0.72, 1.0), 1.15,
		"The wind that holds the Reach together. Where it blows hardest, the islands stay up; where it stops, they fall."],
	[&"nocthea", &"astrarch", "Nocthea, the Eclipsed Star", Color(0.62, 0.6, 0.78), 1.12,
		"The moon the vault was built to hold. She has been dark so long she has forgotten she was ever bright."],
	[&"solmara", &"forgemaster", "Solmara, the Drowned Sun", Color(1.0, 0.78, 0.45), 1.15,
		"The temple's sun-priestess, burning under the sea for six hundred years. The water boils around her and she does not notice."],
]

## The five lords, copied from their templates in `existing` (DataEnemies.build's list).
static func defs(existing: Array) -> Array:
	var by_id := {}
	for e: EnemyDef in existing:
		by_id[e.id] = e
	var out := []
	for row in LORDS:
		var src: EnemyDef = by_id.get(row[1])
		if src == null:
			push_warning("DataEnemiesSpecial: template boss %s is missing" % row[1])
			continue
		var e := src.duplicate(true) as EnemyDef
		e.id = row[0]
		e.display_name = row[2]
		e.tint = row[3]
		e.model_scale = src.model_scale * float(row[4])
		e.body_radius = src.body_radius * float(row[4])
		e.body_height = src.body_height * float(row[4])
		e.hp = src.hp * HP
		e.damage_min = src.damage_min * DAMAGE
		e.damage_max = src.damage_max * DAMAGE
		e.lore = row[5]
		out.append(e)
	return out
