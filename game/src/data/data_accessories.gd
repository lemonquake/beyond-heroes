class_name DataAccessories
## bh-027: twenty new accessories — seven rings, seven amulets and six charms, each its own shape (models from
## tools/blender/items/item_gear.py, worn on the hero by tools/blender/hero/hero_wear_ends.py) with its own implicit.
## Accessories suit every class: they drop from monsters and chests alongside weapons (Loot.equipment_for).
##
## Row: [id, name, model kind (docs), level, value, implicit mods, lore].

const ICON3D := "res://assets/ui/icons/items3d/%s.png"

static func rows() -> Array:
	return [
		# ---- rings ------------------------------------------------------------------------------------------------
		[&"kingsguard_crown_ring", "Kingsguard Crown Ring", "ring/crown", 6, 45, [StatModifier.inc(&"max_hp", 0.04), StatModifier.flat(&"block_chance", 0.02)],
			"Six gold prongs hold a ruby the size of a lentil. Every guard of the old keep wore one, and every one of them held the gate."],
		[&"viper_coil_ring", "Coil of the Viper", "ring/serpent", 14, 70, [StatModifier.inc(&"dot_damage", 0.12), StatModifier.flat(&"crit_chance", 0.01)],
			"A brass serpent swallowing its own tail. Its emerald eyes never close."],
		[&"twinmoon_band", "Twinmoon Band", "ring/double", 20, 85, [StatModifier.flat(&"mana_regen", 1.5), StatModifier.inc(&"max_mana", 0.05)],
			"Two bands, silver and moonsteel, joined by a single pearl — made for a pair of sisters who were never apart."],
		[&"starcluster_ring", "Starcluster Ring", "ring/cluster", 26, 110, [StatModifier.inc(&"elemental_damage", 0.06), StatModifier.flat(&"pen_elemental", 0.03)],
			"Three stones for the three stars sailors steer by: blue for the sea, gold for the harbour, violet for home."],
		[&"thornbrand_ring", "Thornbrand Ring", "ring/spiked", 32, 130, [StatModifier.flat(&"thorns", 25.0), StatModifier.inc(&"phys_damage", 0.05)],
			"Black iron ringed with thorns. Shaking hands with its wearer is a mistake made exactly once."],
		[&"gravewhisper_ring", "Gravewhisper Ring", "ring/skull", 38, 150, [StatModifier.flat(&"life_leech", 0.012), StatModifier.flat(&"hp_on_kill", 12.0)],
			"A bone skull no bigger than a pea. At night its sockets glow, and it whispers the names of the fallen."],
		[&"tidecaller_moonstone", "Tidecaller's Moonstone", "ring/moonstone", 44, 175, [StatModifier.inc(&"healing", 0.10), StatModifier.flat(&"cdr", 0.04)],
			"The stone rises and falls with the tide, however far from the sea it is carried."],
		# ---- amulets ----------------------------------------------------------------------------------------------
		[&"sunforged_medallion", "Sunforged Medallion", "amulet/sun", 3, 35, [StatModifier.inc(&"damage", 0.03)],
			"Hammered from a temple bell after the temple fell. It is always warm."],
		[&"crescent_nighttide", "Crescent of the Night Tide", "amulet/crescent", 9, 55, [StatModifier.flat(&"evasion", 22.0), StatModifier.inc(&"move_speed", 0.03)],
			"Smugglers of the Salted Coast wore the crescent so the moon would look the other way."],
		[&"watchers_eye", "Watcher's Eye", "amulet/eye", 17, 80, [StatModifier.flat(&"accuracy", 35.0), StatModifier.flat(&"crit_chance", 0.02)],
			"The Lantern Covenant's first archivist carved it so something would keep reading while she slept."],
		[&"bulwark_locket", "Bulwark Locket", "amulet/locket", 24, 100, [StatModifier.flat(&"defense", 30.0), StatModifier.flat(&"knockback_res", 0.06)],
			"A tiny shield on a chain. Inside, a lock of hair from someone worth coming home to."],
		[&"windrider_feather", "Windrider Feather", "amulet/feather", 30, 120, [StatModifier.inc(&"move_speed", 0.06), StatModifier.inc(&"projectile_speed", 0.12)],
			"Cast from the flight feather of a storm eagle. Arrows loosed near it fly as if late for something."],
		[&"wolfclaw_torc", "Wolfclaw Torc", "amulet/claws", 36, 140, [StatModifier.inc(&"attack_speed", 0.05), StatModifier.flat(&"life_leech", 0.01)],
			"Three claws from the pack-mother of the Ruined Forest, taken by the only hunter she did not eat."],
		[&"phial_of_last_light", "Phial of Last Light", "amulet/vial", 50, 210, [StatModifier.inc(&"potion_power", 0.20), StatModifier.flat(&"hp_regen", 4.0)],
			"A mouthful of dawn, bottled in the last hour before the Spire went dark."],
		# ---- charms -----------------------------------------------------------------------------------------------
		[&"wayfarers_knot", "Wayfarer's Knot", "charm/knot", 2, 30, [StatModifier.inc(&"xp_gain", 0.05), StatModifier.inc(&"move_speed", 0.02)],
			"Three loops, no end. Travellers tie one on for every road they mean to walk back along."],
		[&"gamblers_bones", "Gambler's Bones", "charm/dice", 11, 60, [StatModifier.flat(&"magic_find", 0.10), StatModifier.inc(&"gold_find", 0.12)],
			"Loaded? Of course they are loaded. The question is in whose favour."],
		[&"spirit_bell", "Spirit Bell", "charm/bell", 19, 85, [StatModifier.inc(&"tempo_damage", 0.12), StatModifier.inc(&"aura_effect", 0.06)],
			"Its ring is too high for living ears. The Tempo spirits hear it well enough, and come."],
		[&"stoneheart_idol", "Stoneheart Idol", "charm/idol", 28, 115, [StatModifier.inc(&"max_hp", 0.05), StatModifier.flat(&"status_res", 0.05)],
			"A squat little god of the hill clans. It asks for nothing and gives the one thing it has: stubbornness."],
		[&"verdant_leaf_charm", "Verdant Leaf Charm", "charm/leaf", 34, 135, [StatModifier.flat(&"hp_regen", 3.0), StatModifier.inc(&"healing", 0.08)],
			"A leaf from the last green tree of the fallen village, dipped in resin so it never browns."],
		[&"sands_of_tempo", "Sands of Tempo", "charm/hourglass", 55, 240, [StatModifier.flat(&"cdr", 0.05), StatModifier.flat(&"mana_cost_reduction", 0.05)],
			"The sand inside falls upward when a spirit is near. Nobody has ever seen it run out."],
	]

static func ids() -> Array:
	return rows().map(func(r): return r[0])

static func bases() -> Array:
	var out := []
	for r in rows():
		var b := DataItems._b(r[0], r[1], &"accessory", "", {"level_req": int(r[3]), "value": int(r[4]), "implicit": r[5], "lore": String(r[6])})
		b.icon = ICON3D % String(r[0])
		out.append(b)
	return out

## The accessory's shape family ("ring", "amulet" or "charm").
static func kind(id: StringName) -> String:
	for r in rows():
		if r[0] == id:
			return String(r[2]).get_slice("/", 0)
	return ""
