class_name DataCrystals
## bh-018: socket crystals. Eight families x four grades (Fragment < Shard < Crystalline < Orbital), set into the sockets a
## Socket Specialist opens in equipment (Sockets, SocketWindow). What a crystal gives depends on where it is set:
## a weapon, armour (helm, inner garment, armour, gloves, boots, shield) or jewellery (accessories). Bloodrift and
## Essencerift fit weapons only. Aetherift is the rare one: strong stats and a rare passive in every kind of gear.
## Crystals come from bosses (always), minibosses (always, Fragment or Shard) and the Socket Specialists' shops (dear).

const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC

const GRADES: Array[StringName] = [&"fragment", &"shard", &"crystalline", &"orbital"]
const GRADE_NAMES := ["Fragment", "Shard", "Crystalline", "Orbital"]
## Colour tier of each grade in names and loot beams (Aetherift one tier higher).
const GRADE_RARITY := [BH.Rarity.ADVANCED, BH.Rarity.ELITE, BH.Rarity.MYTHICAL, BH.Rarity.LEGENDARY]
## Shop price of one crystal; Aetherift costs AETHER_PRICE_MULT times as much.
const PRICE := [5000, 15000, 45000, 135000]
const AETHER_PRICE_MULT := 3

const WEAPON := &"weapon"
const ARMOR := &"armor"
const JEWEL := &"jewel"
const GROUP_NAMES := {WEAPON: "In a weapon", ARMOR: "In armour", JEWEL: "In jewellery"}

## family -> {name, color, blurb, weapon_only, weapon/armor/jewel: [[stat, op, [fragment, shard, crystalline, orbital]], ...],
##            passive: {group: [flag, [magnitudes], name, description with %s]}}
const FAMILIES := {
	&"ember": {"name": "Ember", "color": Color(1.0, 0.45, 0.16), "blurb": "Fire caught in stone.",
		WEAPON: [[&"added_fire", F, [4, 10, 20, 38]]],
		ARMOR: [[&"res_fire", F, [0.05, 0.09, 0.14, 0.20]]],
		JEWEL: [[&"dmg_fire", I, [0.06, 0.12, 0.20, 0.32]], [&"burn_damage", F, [0.04, 0.08, 0.13, 0.20]]]},
	&"aqua": {"name": "Aqua", "color": Color(0.25, 0.62, 1.0), "blurb": "A drop of the deep sea that never dries.",
		WEAPON: [[&"added_water", F, [4, 10, 20, 38]]],
		ARMOR: [[&"res_water", F, [0.05, 0.09, 0.14, 0.20]], [&"max_hp", F, [8, 20, 40, 70]]],
		JEWEL: [[&"mana_regen", F, [0.5, 1.2, 2.2, 3.8]], [&"healing", F, [0.03, 0.06, 0.10, 0.15]]]},
	&"nova": {"name": "Nova", "color": Color(1.0, 0.9, 0.55), "blurb": "Starlight that fell and hardened.",
		WEAPON: [[&"added_light", F, [4, 10, 20, 38]]],
		ARMOR: [[&"res_light", F, [0.04, 0.07, 0.11, 0.16]], [&"res_dark", F, [0.04, 0.07, 0.11, 0.16]]],
		JEWEL: [[&"crit_chance", F, [0.01, 0.02, 0.035, 0.05]]]},
	&"thundra": {"name": "Thundra", "color": Color(1.0, 0.92, 0.3), "blurb": "A thunderhead's heart, still crackling.",
		WEAPON: [[&"added_lightning", F, [3, 9, 19, 36]]],
		ARMOR: [[&"res_lightning", F, [0.05, 0.09, 0.14, 0.20]]],
		JEWEL: [[&"attack_speed", I, [0.02, 0.04, 0.07, 0.10]], [&"cast_speed", I, [0.02, 0.04, 0.07, 0.10]]]},
	&"vipera": {"name": "Vipera", "color": Color(0.45, 0.95, 0.3), "blurb": "Venom, crystallised in a serpent's eye.",
		WEAPON: [[&"poison_on_hit", F, [8, 16, 28, 45]], [&"dot_damage", F, [0.05, 0.10, 0.16, 0.25]]],
		ARMOR: [[&"status_res", F, [0.03, 0.06, 0.09, 0.13]], [&"thorns", F, [4, 10, 20, 35]]],
		JEWEL: [[&"dot_damage", F, [0.06, 0.12, 0.20, 0.30]]]},
	&"bloodrift": {"name": "Bloodrift", "color": Color(0.85, 0.1, 0.16), "blurb": "A rift that drinks. Weapons only.", "weapon_only": true,
		WEAPON: [[&"life_leech", F, [0.01, 0.02, 0.035, 0.055]], [&"hp_on_kill", F, [2, 5, 10, 18]]]},
	&"essencerift": {"name": "Essencerift", "color": Color(0.45, 0.45, 1.0), "blurb": "A rift that drinks the mind. Weapons only.", "weapon_only": true,
		WEAPON: [[&"mana_leech", F, [0.01, 0.02, 0.035, 0.055]], [&"mana_on_hit", F, [0.5, 1.0, 2.0, 3.0]]]},
	&"aetherift": {"name": "Aetherift", "color": Color(0.7, 0.95, 1.0), "blurb": "A tear in the world, full of light. Very rare.",
		WEAPON: [[&"damage", I, [0.05, 0.09, 0.14, 0.20]], [&"crit_damage", F, [0.08, 0.14, 0.22, 0.32]]],
		ARMOR: [[&"res_all", F, [0.03, 0.05, 0.08, 0.12]], [&"max_hp", F, [15, 35, 65, 110]]],
		JEWEL: [[&"cdr", F, [0.02, 0.03, 0.05, 0.07]], [&"elemental_damage", I, [0.05, 0.09, 0.14, 0.20]], [&"skill_levels", F, [0, 0, 0, 1]]],
		"passive": {
			WEAPON: [&"crit_lightning", [0.15, 0.25, 0.35, 0.5], "Riftborn Echo", "Critical attacks release chain lightning at up to 3 nearby enemies (%s of the hit as Lightning)."],
			ARMOR: [&"low_hp_dr", [0.04, 0.07, 0.10, 0.14], "Rift Bulwark", "While below 35%% HP you take %s less damage."],
			JEWEL: [&"crit_cdr", [0.1, 0.2, 0.3, 0.5], "Rift Tempo", "Critical hits cut every skill cooldown by %s."],
		}},
}
const ORDER: Array[StringName] = [&"ember", &"aqua", &"nova", &"thundra", &"vipera", &"bloodrift", &"essencerift", &"aetherift"]

## Maximum sockets per equipment tier (rarity): Beginner and Common 1 ... Aether 7.
const MAX_SOCKETS := [1, 1, 2, 3, 3, 4, 5, 6, 6, 7]

const ICON := "res://assets/ui/icons/crystals/%s.png"

static func id_of(family: StringName, grade: int) -> StringName:
	return StringName("%s_%s" % [family, GRADES[clampi(grade, 0, 3)]])

static func is_crystal(base_id: StringName) -> bool:
	return family_of(base_id) != &""

static func family_of(base_id: StringName) -> StringName:
	var s := String(base_id)
	for f in ORDER:
		if s.begins_with(String(f) + "_") and GRADES.has(StringName(s.substr(String(f).length() + 1))):
			return f
	return &""

static func grade_of(base_id: StringName) -> int:
	var f := family_of(base_id)
	if f == &"":
		return -1
	return GRADES.find(StringName(String(base_id).substr(String(f).length() + 1)))

static func name_of(family: StringName, grade: int) -> String:
	return "%s %s" % [FAMILIES[family].name, GRADE_NAMES[clampi(grade, 0, 3)]]

static func weapon_only(family: StringName) -> bool:
	return bool(FAMILIES.get(family, {}).get("weapon_only", false))

static func price(base_id: StringName) -> int:
	var g := grade_of(base_id)
	if g < 0:
		return 0
	return PRICE[g] * (AETHER_PRICE_MULT if family_of(base_id) == &"aetherift" else 1)

## Which crystal effects a piece of equipment takes (weapon / armour / jewellery), or &"" for non-equipment.
static func group_for(category: StringName) -> StringName:
	match category:
		&"weapon": return WEAPON
		&"accessory": return JEWEL
		&"shield", &"helm", &"inner_garment", &"armor", &"gloves", &"boots": return ARMOR
	return &""

## The stat modifiers one crystal grants in a piece of the given category.
static func mods(base_id: StringName, category: StringName, source := "") -> Array:
	var out: Array = []
	var f := family_of(base_id)
	var g := grade_of(base_id)
	var grp := group_for(category)
	if f == &"" or grp == &"":
		return out
	var fd: Dictionary = FAMILIES[f]
	var src := source if source != "" else name_of(f, g)
	for e in fd.get(grp, []):
		var v := float(e[2][g])
		if v != 0.0:
			out.append(StatModifier.new(e[0], e[1], v, src))
	var pv: Array = fd.get("passive", {}).get(grp, [])
	if not pv.is_empty():
		out.append(StatModifier.flat(StringName("flag_" + String(pv[0])), float(pv[1][g]), src))
	return out

## Tooltip lines for one crystal in one group: stat lines then the passive (name, text).
static func lines(base_id: StringName, grp: StringName) -> PackedStringArray:
	var out := PackedStringArray()
	var f := family_of(base_id)
	var g := grade_of(base_id)
	if f == &"":
		return out
	var fd: Dictionary = FAMILIES[f]
	for e in fd.get(grp, []):
		var v := float(e[2][g])
		if v != 0.0:
			out.append(StatDefs.format_modifier(e[0], e[1], v))
	var pv: Array = fd.get("passive", {}).get(grp, [])
	if not pv.is_empty():
		out.append("%s: %s" % [pv[2], passive_text(pv, g)])
	return out

static func passive_text(pv: Array, g: int) -> String:
	var mag := float(pv[1][g])
	var shown := ("%.1f s" % mag) if pv[0] == &"crit_cdr" else ("%d%%" % roundi(mag * 100.0))
	return String(pv[3]) % shown

## Everything a crystal can do, for the crystal's own tooltip and the item catalogue.
static func describe(base_id: StringName) -> PackedStringArray:
	var out := PackedStringArray()
	var f := family_of(base_id)
	for grp in [WEAPON, ARMOR, JEWEL]:
		if f != &"" and weapon_only(f) and grp != WEAPON:
			continue
		var ls := lines(base_id, grp)
		if ls.is_empty():
			continue
		out.append("%s: %s" % [GROUP_NAMES[grp], "; ".join(ls)])
	return out

## The 32 crystal item bases (called from DataItems.bases).
static func items(out: Array) -> void:
	for f in ORDER:
		var fd: Dictionary = FAMILIES[f]
		for g in 4:
			var b := ItemBaseDef.new()
			b.id = id_of(f, g)
			b.display_name = name_of(f, g)
			b.category = &"crystal"
			b.icon = ICON % b.id
			b.stack_max = 20
			b.weight = 0.1
			b.value = price(b.id)
			b.fixed_rarity = mini(GRADE_RARITY[g] + (1 if f == &"aetherift" else 0), BH.Rarity.AETHER)
			b.flavor = "%s Set it into a socket at a Socket Specialist." % fd.blurb
			b.lore = fd.blurb
			out.append(b)

# ---- drops -------------------------------------------------------------------------------------------------------

## A random crystal for a kill: bosses may drop any grade (better with level), minibosses a Fragment or a Shard.
## Aetherift is rare (4% from bosses, 1% from minibosses).
static func roll_drop(rng: RandomNumberGenerator, level: int, boss: bool) -> StringName:
	var fam: StringName
	var aether_p := 0.04 if boss else 0.01
	if rng.randf() < aether_p:
		fam = &"aetherift"
	else:
		fam = ORDER[rng.randi_range(0, ORDER.size() - 2)]
	var g := 0
	if boss:
		# weights Fragment/Shard/Crystalline/Orbital shift toward the top as the boss's level rises
		var t := clampf(float(level - 5) / 45.0, 0.0, 1.0)
		var w := [lerpf(45.0, 5.0, t), lerpf(40.0, 30.0, t), lerpf(13.0, 40.0, t), lerpf(2.0, 25.0, t)]
		g = _weighted(rng, w)
	else:
		g = 1 if rng.randf() < clampf(0.25 + float(level) * 0.012, 0.25, 0.6) else 0
	return id_of(fam, g)

static func _weighted(rng: RandomNumberGenerator, w: Array) -> int:
	var total := 0.0
	for x in w:
		total += float(x)
	var r := rng.randf() * total
	for i in w.size():
		r -= float(w[i])
		if r <= 0.0:
			return i
	return w.size() - 1
