class_name DataEnemiesAbyss
## bh-042: the ten bosses of the Abyss (docs/PLAN_bh-042.md, phase 4). Nine are downloaded CC0 creatures put on the
## game's skeleton so they play the whole action library (assets_src/bh042/, rig_to_hero.py), one is the Fallen
## Necro-Knight on the hero body (DataPersonas, NecroKnight). Base stats sit beside the Zarael bosses; the level, the
## Descent and the Abyss (x8 damage, +50% Defense, growing health past 90) do the rest.
## Every one of them carries Curse of Stillness (a sigil where no spell can be cast) and Armour Rip (-60% Defense) and at
## least two bullet patterns (AbyssMoves / Barrage); names are invented (no borrowed real-culture names — user rule).

const F := Elements.FIRE
const I := Elements.ICE
const L := Elements.LIGHTNING
const E := Elements.EARTH
const WI := Elements.WIND
const WA := Elements.WATER
const LT := Elements.LIGHT
const D := Elements.DARK
const MODELS := "res://assets/characters/bh042/%s"

## Display names without building the defs (map hints are written while the database itself is still loading).
const NAMES := {&"fallen_necro_knight": "The Fallen Necro-Knight", &"morvhaal": "Morvhaal, the Ossuary King",
	&"flayed_archivist": "The Flayed Archivist", &"ysolde": "Ysolde, the Faceless", &"thalassor": "Thalassor, the Drowned Colossus",
	&"kharzul": "Kharzul, the Slag Tyrant", &"gorehelm": "Gorehelm the Glutton", &"rimehorn": "Rimehorn, the Last Winter",
	&"weeping_shroud": "The Weeping Shroud", &"vaelgor": "Vaelgor, the Nameless Wyrm"}

## The Necro-Knight's level over the hero's (Spawner.spawn_enemy).
const NECRO_LEVELS_ABOVE := 5

static func e(id: StringName, name: String, d: Dictionary) -> EnemyDef:
	var x := DataEnemies._e(id, name, &"boss", d)
	if d.has("model_file"):
		x.model = MODELS % String(d.model_file)
	return x

## The shared pair: a Curse of Stillness on the hero's spot and an Armour Rip lash (tuned per boss through `over`).
static func curse(el: int, over := {}) -> Dictionary:
	var a := {"id": &"stillness", "anim": &"cast_area", "range": 22.0, "mult": 0.6, "element": el, "knockback": 2.0, "poise": 10.0,
		"cooldown": 16.0, "kind": "curse_zone", "radius": 6.5, "delay": 1.1, "duration": 6.0, "windup": 0.5}
	a.merge(over, true)
	return a

static func rip(el: int, over := {}) -> Dictionary:
	var a := {"id": &"armour_rip", "anim": &"cast_heavy", "range": 16.0, "min_range": 2.0, "mult": 0.9, "element": el, "knockback": 5.0,
		"poise": 20.0, "cooldown": 14.0, "kind": "armor_rip", "speed": 34.0, "windup": 0.7}
	a.merge(over, true)
	return a

static func defs() -> Array:
	return [necro_knight(), morvhaal(), archivist(), ysolde(), thalassor(), kharzul(), gorehelm(), rimehorn(), shroud(), vaelgor()]

static func ids() -> Array[StringName]:
	var out: Array[StringName] = []
	for d: EnemyDef in defs():
		out.append(d.id)
	return out

const BOSS_IMMUNE := [&"frozen", &"stunned", &"feared", &"petrified"]

# ------------------------------------------------------------------------------------------------ 1. the Necro-Knight
static func necro_knight() -> EnemyDef:
	var teal := Color(0.22, 0.95, 0.88)
	return e(&"fallen_necro_knight", "The Fallen Necro-Knight", {"family": &"undead", "role_name": "Fallen hero", "tint": Color(1, 1, 1),
		"hp": 3400.0, "damage_min": 24.0, "damage_max": 34.0, "defense": 80.0, "evasion": 22.0, "accuracy": 80.0, "crit_chance": 0.12,
		"move_speed": 5.2, "weight": 3.0, "poise": 240.0, "knockback_res": 0.7, "status_res": 0.4, "affinity": D,
		"resistances": {D: 0.6, I: 0.3, LT: -0.25, F: 0.1}, "preferred_range": 2.6, "body_radius": 0.55, "body_height": 2.1,
		"model_scale": 1.12, "aggro_range": 30.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE,
		"sight_range": 40.0, "blocks_front": true, "guard_break": 160.0, "traits": [&"player_like"],
		"phases": [{"hp": 1.0, "name": "The Oath Remembered"}, {"hp": 0.6, "name": "The Oath Broken"}, {"hp": 0.3, "name": "Nothing Left to Lose"}],
		"attacks": [
			{"id": &"nk_cut_1", "anim": &"sword_1", "range": 2.6, "mult": 1.0, "knockback": 4.0, "poise": 16.0, "cooldown": 1.6, "kind": "melee", "arc": 120.0, "weight": 2.0},
			{"id": &"nk_cut_2", "anim": &"sword_2", "range": 2.6, "mult": 1.1, "knockback": 5.0, "poise": 18.0, "cooldown": 99.0, "kind": "melee", "arc": 120.0, "weight": 0.0},
			{"id": &"nk_cut_3", "anim": &"sword_heavy", "range": 2.8, "mult": 1.6, "knockback": 9.0, "poise": 34.0, "cooldown": 99.0, "kind": "melee", "arc": 140.0, "weight": 0.0},
			{"id": &"nk_bash", "anim": &"shield_bash", "range": 2.2, "mult": 0.9, "knockback": 10.0, "poise": 40.0, "cooldown": 6.0, "kind": "melee", "arc": 80.0,
				"status": {&"stunned": 120.0}},
			{"id": &"nk_charge", "anim": &"sword_heavy", "range": 14.0, "min_range": 4.0, "mult": 1.3, "knockback": 12.0, "poise": 40.0, "cooldown": 8.0,
				"kind": "dash", "dash": 12.0, "windup": 0.45},
			{"id": &"nk_whirl", "anim": &"whirlwind", "range": 4.5, "mult": 1.2, "element": D, "knockback": 8.0, "poise": 30.0, "cooldown": 9.0, "kind": "aoe",
				"radius": 4.5, "windup": 0.5, "telegraph": "circle", "self_centered": true, "tele_color": Color(teal, 0.7)},
			{"id": &"nk_soulbolt", "anim": &"cast_quick", "range": 20.0, "min_range": 5.0, "mult": 1.0, "element": D, "knockback": 3.0, "poise": 10.0,
				"cooldown": 4.0, "kind": "projectile", "speed": 22.0, "count": 3, "spread": 18.0, "windup": 0.3},
			curse(D, {"cooldown": 15.0, "color": teal}),
			rip(D, {"cooldown": 12.0}),
			{"id": &"nk_soul_spiral", "anim": &"cast_channel", "range": 14.0, "mult": 0.45, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 14.0,
				"kind": "barrage", "pattern": "spiral", "arms": 3, "duration": 2.6, "rate": 8.0, "spin": 140.0, "speed": 10.0, "reach": 24.0,
				"windup": 0.6, "color": teal, "phase": 2},
			{"id": &"nk_death_nova", "anim": &"cast_ultimate", "range": 9.0, "mult": 2.0, "element": D, "knockback": 14.0, "poise": 60.0, "cooldown": 16.0,
				"kind": "aoe", "radius": 9.0, "inner_radius": 3.0, "windup": 1.4, "telegraph": "ring", "self_centered": true, "phase": 2},
			{"id": &"nk_raise", "anim": &"boss_summon", "range": 40.0, "cooldown": 26.0, "kind": "summon", "summon": &"hollow_soldier", "count": 3, "phase": 3},
		],
		"xp_mult": 48.0, "drop_chance": 1.0, "gold": Vector2i(600, 900),
		"loot": [[&"champion_essence", 1.0, 3, 5], [&"aether_shard", 1.0, 3, 5]],
		"sounds": {"hurt": &"hit_armor", "death": &"boss_roar", "idle": &"cultist_chant"}, "hit_material": &"metal", "blood": Color(0.1, 0.5, 0.45),
		"death_style": &"fall", "corpse_time": 60.0,
		"lore": "He was the best of a company that went down into the Abyss and did not come back. He came back. He still fights the way they taught him — the roll, the shield, the draught at the right moment — and he is always a little better than you."})

# ------------------------------------------------------------------------------------------------ 2. Morvhaal
static func morvhaal() -> EnemyDef:
	var bone := Color(0.9, 0.86, 0.72)
	return e(&"morvhaal", "Morvhaal, the Ossuary King", {"family": &"undead", "role_name": "Lord of the Hollow Crown", "model_file": "morvhaal.scn",
		"tint": Color(1, 1, 1), "hp": 4600.0, "damage_min": 26.0, "damage_max": 38.0, "defense": 86.0, "evasion": 4.0, "accuracy": 76.0,
		"move_speed": 3.6, "weight": 14.0, "poise": 360.0, "knockback_res": 0.85, "status_res": 0.4, "affinity": D,
		"resistances": {D: 0.6, I: 0.4, E: 0.2, LT: -0.35, F: -0.15}, "preferred_range": 4.0, "body_radius": 1.4, "body_height": 4.8,
		"model_scale": 1.0, "aggro_range": 34.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE, "sight_range": 44.0,
		"phases": [{"hp": 1.0, "name": "The Court Assembles"}, {"hp": 0.66, "name": "Grave Rings"}, {"hp": 0.33, "name": "The Marrow Crown"}],
		"attacks": [
			{"id": &"bone_rake", "anim": &"boss_sweep", "range": 5.5, "mult": 1.2, "knockback": 12.0, "poise": 40.0, "cooldown": 3.0, "kind": "aoe",
				"radius": 5.5, "arc": 150.0, "windup": 0.8, "telegraph": "cone", "self_centered": true},
			{"id": &"ossuary_slam", "anim": &"boss_slam", "range": 6.0, "mult": 1.8, "element": E, "knockback": 15.0, "poise": 60.0, "cooldown": 7.0,
				"kind": "aoe", "radius": 6.0, "windup": 1.1, "telegraph": "circle", "self_centered": true},
			{"id": &"grave_rings", "anim": &"cast_area", "range": 18.0, "mult": 0.45, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 11.0,
				"kind": "barrage", "pattern": "radial", "count": 28, "waves": 3, "gap": 0.55, "speed": 8.5, "reach": 26.0, "windup": 0.7, "color": bone},
			{"id": &"ossuary_rain", "anim": &"cast_heavy", "range": 22.0, "mult": 1.3, "element": E, "knockback": 4.0, "poise": 14.0, "cooldown": 12.0,
				"kind": "strikes", "count": 6, "delay": 1.2, "radius": 2.2, "windup": 0.5, "phase": 2},
			curse(D),
			rip(D),
			{"id": &"raise_the_court", "anim": &"boss_summon", "range": 40.0, "cooldown": 24.0, "kind": "summon", "summon": &"hollow_soldier", "count": 4, "phase": 2},
			{"id": &"marrow_spiral", "anim": &"cast_channel", "range": 16.0, "mult": 0.4, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 14.0,
				"kind": "barrage", "pattern": "spiral", "arms": 5, "duration": 3.2, "rate": 6.0, "spin": 90.0, "speed": 9.0, "reach": 26.0,
				"windup": 0.8, "color": bone, "phase": 3},
		],
		"xp_mult": 60.0, "drop_chance": 1.0, "gold": Vector2i(900, 1300),
		"loot": [[&"bone_fragment", 1.0, 4, 6], [&"champion_essence", 1.0, 3, 5]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"ghoul_growl"}, "hit_material": &"bone", "death_style": &"crumple",
		"corpse_time": 60.0,
		"lore": "The vault's first king, buried with his court. He got up when the Abyss opened beneath his crypt, and he made the court get up with him."})

# ------------------------------------------------------------------------------------------------ 3. the Flayed Archivist
static func archivist() -> EnemyDef:
	var ink := Color(0.85, 0.15, 0.2)
	return e(&"flayed_archivist", "The Flayed Archivist", {"family": &"corrupted", "role_name": "Warden of the Hollow Crown", "model_file": "flayed_archivist.scn",
		"tint": Color(1, 1, 1), "hp": 3600.0, "damage_min": 22.0, "damage_max": 32.0, "defense": 60.0, "evasion": 18.0, "accuracy": 74.0,
		"move_speed": 4.6, "weight": 8.0, "poise": 260.0, "knockback_res": 0.7, "status_res": 0.35, "affinity": D,
		"resistances": {D: 0.5, F: -0.3, LT: -0.2, WA: 0.2}, "preferred_range": 6.0, "body_radius": 1.0, "body_height": 3.8,
		"model_scale": 1.0, "aggro_range": 32.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE, "sight_range": 42.0,
		"phases": [{"hp": 1.0, "name": "The Index"}, {"hp": 0.6, "name": "Page Storm"}, {"hp": 0.3, "name": "The Unwritten"}],
		"attacks": [
			{"id": &"flay", "anim": &"dagger_1", "range": 3.2, "mult": 1.0, "knockback": 4.0, "poise": 16.0, "cooldown": 1.8, "kind": "melee", "arc": 130.0,
				"status": {&"bleeding": 60.0}},
			{"id": &"flay_twice", "anim": &"dual_heavy", "range": 3.2, "mult": 1.5, "knockback": 7.0, "poise": 26.0, "cooldown": 5.0, "kind": "melee", "arc": 160.0},
			{"id": &"page_storm", "anim": &"cast_quick", "range": 22.0, "mult": 0.42, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 8.0,
				"kind": "barrage", "pattern": "fan", "count": 11, "spread": 80.0, "waves": 5, "gap": 0.32, "speed": 11.0, "reach": 28.0, "windup": 0.5, "color": ink},
			{"id": &"flayed_script", "anim": &"cast_channel", "range": 16.0, "mult": 0.4, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 13.0,
				"kind": "barrage", "pattern": "cross", "duration": 3.0, "rate": 9.0, "spin": 45.0, "speed": 10.0, "reach": 24.0, "windup": 0.6, "color": ink, "phase": 2},
			curse(D, {"radius": 8.0, "cooldown": 12.0}),
			rip(D),
			{"id": &"unwritten", "anim": &"cast_ultimate", "range": 24.0, "mult": 0.7, "element": D, "knockback": 3.0, "poise": 10.0, "cooldown": 12.0,
				"kind": "barrage", "pattern": "homing", "count": 8, "gap": 0.1, "homing": 110.0, "seek": 3.0, "speed": 6.5, "reach": 30.0,
				"windup": 0.8, "color": Color(0.95, 0.9, 0.85), "shot_radius": 0.5, "phase": 3},
		],
		"abilities": [{"id": &"blink", "kind": "teleport", "cooldown": 9.0, "range": 8.0}],
		"xp_mult": 44.0, "drop_chance": 1.0, "gold": Vector2i(600, 900),
		"loot": [[&"champion_essence", 1.0, 2, 4], [&"aether_shard", 1.0, 2, 3]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"cultist_chant"}, "hit_material": &"flesh", "blood": Color(0.45, 0.02, 0.04),
		"corpse_time": 45.0,
		"lore": "The vault's record-keeper took his work too far: he wrote the names of the dead on himself, and when he ran out of skin he kept going."})

# ------------------------------------------------------------------------------------------------ 4. Ysolde
static func ysolde() -> EnemyDef:
	var steel := Color(0.75, 0.95, 1.0)
	return e(&"ysolde", "Ysolde, the Faceless", {"family": &"corrupted", "role_name": "Warden of the Sunless Cistern", "model_file": "ysolde.scn",
		"tint": Color(1, 1, 1), "hp": 3000.0, "damage_min": 22.0, "damage_max": 30.0, "defense": 48.0, "evasion": 40.0, "accuracy": 86.0,
		"crit_chance": 0.15, "move_speed": 6.2, "weight": 5.0, "poise": 200.0, "knockback_res": 0.6, "status_res": 0.35, "affinity": WA,
		"resistances": {WA: 0.5, I: 0.3, D: 0.3, L: -0.35}, "preferred_range": 2.4, "body_radius": 0.8, "body_height": 3.5, "flanker": true,
		"model_scale": 1.0, "aggro_range": 32.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE, "sight_range": 44.0,
		"phases": [{"hp": 1.0, "name": "A Knife in the Dark"}, {"hp": 0.6, "name": "The Thousand Knives"}, {"hp": 0.3, "name": "Night Lattice"}],
		"attacks": [
			{"id": &"cut", "anim": &"dagger_1", "range": 2.6, "mult": 0.9, "knockback": 3.0, "poise": 12.0, "cooldown": 1.2, "kind": "melee", "arc": 110.0,
				"status": {&"bleeding": 50.0}},
			{"id": &"lunge", "anim": &"dagger_heavy", "range": 12.0, "min_range": 3.5, "mult": 1.4, "knockback": 6.0, "poise": 20.0, "cooldown": 4.5,
				"kind": "dash", "dash": 10.0, "windup": 0.35},
			{"id": &"thousand_knives", "anim": &"cast_weapon", "range": 22.0, "mult": 0.45, "element": WA, "knockback": 2.0, "poise": 6.0, "cooldown": 10.0,
				"kind": "barrage", "pattern": "wall", "waves": 4, "gap_time": 0.85, "width": 20.0, "spacing": 1.0, "gap": 3.2, "speed": 10.0,
				"reach": 30.0, "windup": 0.6, "color": steel, "shot_radius": 0.3},
			{"id": &"fan_of_knives", "anim": &"dual_heavy", "range": 16.0, "mult": 0.5, "knockback": 2.0, "poise": 6.0, "cooldown": 6.0,
				"kind": "barrage", "pattern": "fan", "count": 7, "spread": 60.0, "waves": 2, "gap": 0.25, "speed": 16.0, "reach": 22.0, "windup": 0.35,
				"color": steel, "shot_radius": 0.28},
			curse(WA),
			rip(WA, {"cooldown": 9.0, "mult": 1.0}),
			{"id": &"night_lattice", "anim": &"cast_ultimate", "range": 14.0, "mult": 0.4, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 13.0,
				"kind": "barrage", "pattern": "orbit", "count": 20, "waves": 4, "gap": 0.4, "curve": 55.0, "speed": 7.5, "reach": 26.0,
				"windup": 0.7, "color": Color(0.5, 0.4, 1.0), "phase": 3},
		],
		"abilities": [{"id": &"vanish", "kind": "teleport", "cooldown": 7.0, "range": 9.0}],
		"xp_mult": 44.0, "drop_chance": 1.0, "gold": Vector2i(600, 900),
		"loot": [[&"shadow_silk", 1.0, 2, 4], [&"champion_essence", 1.0, 2, 4]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"cultist_chant"}, "hit_material": &"shadow", "death_style": &"smoke",
		"corpse_time": 30.0,
		"lore": "The cistern's keepers wore masks so the drowned would not know them. Ysolde wore hers until it grew into her. She has no face now, and no mercy either."})

# ------------------------------------------------------------------------------------------------ 5. Thalassor
static func thalassor() -> EnemyDef:
	var tide := Color(0.25, 0.85, 0.75)
	return e(&"thalassor", "Thalassor, the Drowned Colossus", {"family": &"beast", "role_name": "Lord of the Sunless Cistern", "model_file": "thalassor.scn",
		"tint": Color(1, 1, 1), "hp": 5200.0, "damage_min": 28.0, "damage_max": 40.0, "defense": 92.0, "evasion": 3.0, "accuracy": 74.0,
		"move_speed": 3.4, "weight": 18.0, "poise": 420.0, "knockback_res": 0.9, "status_res": 0.45, "affinity": WA,
		"resistances": {WA: 0.6, I: 0.3, E: 0.3, L: -0.35, F: 0.2}, "preferred_range": 5.0, "body_radius": 2.0, "body_height": 6.0,
		"model_scale": 1.0, "aggro_range": 36.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE, "sight_range": 46.0,
		"phases": [{"hp": 1.0, "name": "The Black Water"}, {"hp": 0.66, "name": "Undertow"}, {"hp": 0.33, "name": "The Cistern Overflows"}],
		"attacks": [
			{"id": &"crush", "anim": &"boss_slam", "range": 6.5, "mult": 1.9, "element": WA, "knockback": 16.0, "poise": 60.0, "cooldown": 6.5, "kind": "aoe",
				"radius": 6.5, "windup": 1.1, "telegraph": "circle", "self_centered": true, "status": {&"wet": 100.0}},
			{"id": &"backhand", "anim": &"boss_sweep", "range": 6.0, "mult": 1.2, "knockback": 14.0, "poise": 40.0, "cooldown": 3.2, "kind": "aoe",
				"radius": 6.0, "arc": 160.0, "windup": 0.85, "telegraph": "cone", "self_centered": true},
			{"id": &"tidal_ring", "anim": &"cast_area", "range": 18.0, "mult": 0.42, "element": WA, "knockback": 3.0, "poise": 6.0, "cooldown": 10.0,
				"kind": "barrage", "pattern": "orbit", "count": 26, "waves": 3, "gap": 0.6, "curve": 40.0, "speed": 8.0, "reach": 28.0, "windup": 0.8, "color": tide},
			{"id": &"wade", "anim": &"boss_charge", "range": 18.0, "min_range": 6.0, "mult": 1.6, "knockback": 18.0, "poise": 60.0, "cooldown": 11.0,
				"kind": "charge", "width": 3.6, "windup": 1.0, "telegraph": "line", "speed": 12.0},
			{"id": &"undertow", "anim": &"cast_heavy", "range": 20.0, "mult": 0.5, "element": WA, "knockback": 1.0, "poise": 4.0, "cooldown": 14.0,
				"kind": "pools", "count": 4, "radius": 3.0, "duration": 7.0, "windup": 0.6, "phase": 2},
			curse(WA),
			rip(WA),
			{"id": &"overflow", "anim": &"cast_channel", "range": 16.0, "mult": 0.4, "element": WA, "knockback": 2.0, "poise": 6.0, "cooldown": 13.0,
				"kind": "barrage", "pattern": "spiral", "arms": 6, "duration": 3.5, "rate": 5.0, "spin": -70.0, "speed": 8.5, "reach": 28.0,
				"windup": 0.8, "color": tide, "phase": 3},
		],
		"xp_mult": 64.0, "drop_chance": 1.0, "gold": Vector2i(1000, 1400),
		"loot": [[&"tide_pearl", 1.0, 3, 5], [&"champion_essence", 1.0, 3, 5]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"ghoul_growl"}, "hit_material": &"stone", "blood": Color(0.1, 0.25, 0.22),
		"corpse_time": 60.0,
		"lore": "The cistern was built around it while it slept. The water rose for a thousand years, and it grew a reef on its back waiting for the water to go down. It has stopped waiting."})

# ------------------------------------------------------------------------------------------------ 6. Kharzul
static func kharzul() -> EnemyDef:
	var slag := Color(1.0, 0.45, 0.1)
	return e(&"kharzul", "Kharzul, the Slag Tyrant", {"family": &"construct", "role_name": "Lord of the Ashgrave Foundry", "model_file": "kharzul.scn",
		"tint": Color(1, 1, 1), "hp": 5000.0, "damage_min": 28.0, "damage_max": 40.0, "defense": 100.0, "evasion": 2.0, "accuracy": 72.0,
		"move_speed": 3.2, "weight": 18.0, "poise": 440.0, "knockback_res": 0.9, "status_res": 0.45, "affinity": F,
		"resistances": {F: 0.7, E: 0.4, D: 0.2, WA: -0.4, I: -0.25}, "preferred_range": 4.5, "body_radius": 1.7, "body_height": 5.2,
		"model_scale": 1.0, "aggro_range": 34.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE + [&"burning"],
		"sight_range": 44.0,
		"phases": [{"hp": 1.0, "name": "The Furnace Wakes"}, {"hp": 0.66, "name": "Slag Tide"}, {"hp": 0.33, "name": "Meltdown"}],
		"attacks": [
			{"id": &"slag_fist", "anim": &"boss_sweep", "range": 5.5, "mult": 1.3, "element": F, "knockback": 14.0, "poise": 44.0, "cooldown": 3.0, "kind": "aoe",
				"radius": 5.5, "arc": 150.0, "windup": 0.85, "telegraph": "cone", "self_centered": true, "status": {&"burning": 60.0}},
			{"id": &"forge_slam", "anim": &"boss_slam", "range": 6.0, "mult": 2.0, "element": F, "knockback": 16.0, "poise": 60.0, "cooldown": 7.0, "kind": "aoe",
				"radius": 6.0, "windup": 1.1, "telegraph": "circle", "self_centered": true, "status": {&"armor_broken": 70.0}},
			{"id": &"slag_waves", "anim": &"cast_area", "range": 18.0, "mult": 0.45, "element": F, "knockback": 3.0, "poise": 6.0, "cooldown": 10.0,
				"kind": "barrage", "pattern": "radial", "count": 24, "waves": 4, "gap": 0.5, "turn": 7.5, "speed": 9.0, "reach": 26.0, "windup": 0.8, "color": slag},
			{"id": &"eruptions", "anim": &"cast_heavy", "range": 22.0, "mult": 1.4, "element": F, "knockback": 6.0, "poise": 16.0, "cooldown": 9.0,
				"kind": "strikes", "count": 7, "delay": 1.1, "radius": 2.4, "windup": 0.5},
			{"id": &"magma_pools", "anim": &"cast_area", "range": 18.0, "mult": 0.5, "element": F, "knockback": 1.0, "poise": 4.0, "cooldown": 15.0,
				"kind": "pools", "count": 3, "radius": 3.2, "duration": 8.0, "windup": 0.6, "phase": 2},
			curse(F),
			rip(F),
			{"id": &"molten_orbit", "anim": &"cast_channel", "range": 14.0, "mult": 0.4, "element": F, "knockback": 2.0, "poise": 6.0, "cooldown": 12.0,
				"kind": "barrage", "pattern": "orbit", "count": 18, "waves": 5, "gap": 0.45, "curve": -60.0, "speed": 7.0, "reach": 26.0,
				"windup": 0.7, "color": slag, "phase": 3},
		],
		"xp_mult": 64.0, "drop_chance": 1.0, "gold": Vector2i(1000, 1400),
		"loot": [[&"ember_core", 1.0, 3, 5], [&"slag_ember", 1.0, 3, 5]],
		"sounds": {"hurt": &"hit_armor", "death": &"boss_roar", "idle": &"teleporter_hum"}, "hit_material": &"stone", "death_style": &"implode",
		"corpse_time": 60.0,
		"lore": "The foundry poured one last thing before its fires died: a master for itself. Kharzul still works the forges, and anything that walks in is ore."})

# ------------------------------------------------------------------------------------------------ 7. Gorehelm
static func gorehelm() -> EnemyDef:
	var bile := Color(0.75, 0.9, 0.2)
	return e(&"gorehelm", "Gorehelm the Glutton", {"family": &"corrupted", "role_name": "Warden of the Ashgrave Foundry", "model_file": "gorehelm.scn",
		"tint": Color(1, 1, 1), "hp": 4200.0, "damage_min": 26.0, "damage_max": 36.0, "defense": 70.0, "evasion": 4.0, "accuracy": 70.0,
		"move_speed": 4.0, "weight": 16.0, "poise": 380.0, "knockback_res": 0.85, "status_res": 0.4, "affinity": E,
		"resistances": {E: 0.5, F: 0.3, D: 0.2, WI: -0.3, LT: -0.2}, "preferred_range": 3.6, "body_radius": 1.8, "body_height": 4.4,
		"model_scale": 1.0, "aggro_range": 32.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE + [&"poisoned"],
		"sight_range": 42.0,
		"phases": [{"hp": 1.0, "name": "Hungry"}, {"hp": 0.6, "name": "Ravenous"}, {"hp": 0.3, "name": "The Gorging"}],
		"attacks": [
			{"id": &"maw", "anim": &"axe_heavy", "range": 4.0, "mult": 1.6, "knockback": 8.0, "poise": 30.0, "cooldown": 2.6, "kind": "melee", "arc": 120.0,
				"status": {&"bleeding": 70.0}},
			{"id": &"maw_pull", "anim": &"cast_heavy", "range": 12.0, "min_range": 4.0, "mult": 0.8, "knockback": 0.0, "poise": 10.0, "cooldown": 8.0,
				"kind": "tongue", "pull": 9.0, "windup": 0.5, "tongue_color": Color(0.6, 0.15, 0.15)},
			{"id": &"gorge", "anim": &"boss_charge", "range": 16.0, "min_range": 5.0, "mult": 1.6, "knockback": 16.0, "poise": 50.0, "cooldown": 9.0,
				"kind": "charge", "width": 3.4, "windup": 0.9, "telegraph": "line", "speed": 13.0},
			{"id": &"bile_fan", "anim": &"cast_quick", "range": 18.0, "mult": 0.45, "element": E, "knockback": 2.0, "poise": 6.0, "cooldown": 7.0,
				"kind": "barrage", "pattern": "fan", "count": 9, "spread": 70.0, "waves": 4, "gap": 0.3, "speed": 10.0, "reach": 24.0, "windup": 0.5,
				"color": bile, "on_hit_status": {&"poisoned": 4.0}},
			curse(E),
			rip(E),
			{"id": &"bile_seekers", "anim": &"cast_ultimate", "range": 22.0, "mult": 0.6, "element": E, "knockback": 2.0, "poise": 8.0, "cooldown": 12.0,
				"kind": "barrage", "pattern": "homing", "count": 6, "gap": 0.15, "homing": 95.0, "seek": 3.2, "speed": 6.0, "reach": 28.0,
				"windup": 0.8, "color": bile, "shot_radius": 0.55, "phase": 2},
			{"id": &"gorging_slam", "anim": &"boss_slam", "range": 7.0, "mult": 2.2, "element": E, "knockback": 18.0, "poise": 70.0, "cooldown": 12.0,
				"kind": "aoe", "radius": 7.0, "inner_radius": 2.5, "windup": 1.4, "telegraph": "ring", "self_centered": true, "phase": 3},
		],
		"traits": [&"devour"],
		"xp_mult": 50.0, "drop_chance": 1.0, "gold": Vector2i(700, 1000),
		"loot": [[&"champion_essence", 1.0, 2, 4], [&"bone_fragment", 1.0, 3, 5]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"ghoul_growl"}, "hit_material": &"ichor", "blood": Color(0.35, 0.05, 0.03),
		"corpse_time": 45.0,
		"lore": "The foundry's slag-pits never fill up, because something down there eats what is thrown in. It has eaten enough to get up."})

# ------------------------------------------------------------------------------------------------ 8. Rimehorn
static func rimehorn() -> EnemyDef:
	var frost := Color(0.7, 0.92, 1.0)
	return e(&"rimehorn", "Rimehorn, the Last Winter", {"family": &"beast", "role_name": "Lord of the Weeping Bastion", "model_file": "rimehorn.scn",
		"tint": Color(1, 1, 1), "hp": 5100.0, "damage_min": 28.0, "damage_max": 40.0, "defense": 90.0, "evasion": 5.0, "accuracy": 74.0,
		"move_speed": 4.0, "weight": 18.0, "poise": 420.0, "knockback_res": 0.9, "status_res": 0.45, "affinity": I,
		"resistances": {I: 0.7, WA: 0.3, D: 0.2, F: -0.4, L: -0.15}, "preferred_range": 4.5, "body_radius": 1.8, "body_height": 5.6,
		"model_scale": 1.0, "aggro_range": 36.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE + [&"chilled"],
		"sight_range": 46.0,
		"phases": [{"hp": 1.0, "name": "First Frost"}, {"hp": 0.66, "name": "The Long Dark"}, {"hp": 0.33, "name": "The Last Winter"}],
		"attacks": [
			{"id": &"maul", "anim": &"boss_sweep", "range": 6.0, "mult": 1.3, "element": I, "knockback": 14.0, "poise": 44.0, "cooldown": 3.0, "kind": "aoe",
				"radius": 6.0, "arc": 160.0, "windup": 0.85, "telegraph": "cone", "self_centered": true},
			{"id": &"glacier_fall", "anim": &"boss_slam", "range": 6.5, "mult": 2.0, "element": I, "knockback": 16.0, "poise": 60.0, "cooldown": 7.0, "kind": "aoe",
				"radius": 6.5, "windup": 1.2, "telegraph": "circle", "self_centered": true, "status": {&"chilled": 90.0}},
			{"id": &"shard_fan", "anim": &"cast_quick", "range": 20.0, "mult": 0.45, "element": I, "knockback": 2.0, "poise": 6.0, "cooldown": 7.0,
				"kind": "barrage", "pattern": "fan", "count": 13, "spread": 100.0, "waves": 3, "gap": 0.4, "speed": 12.0, "reach": 26.0, "windup": 0.5,
				"color": frost},
			{"id": &"glacier_wall", "anim": &"cast_heavy", "range": 22.0, "mult": 0.5, "element": I, "knockback": 3.0, "poise": 8.0, "cooldown": 11.0,
				"kind": "barrage", "pattern": "wall", "waves": 3, "gap_time": 1.0, "width": 22.0, "spacing": 1.15, "gap": 3.6, "speed": 8.5,
				"reach": 30.0, "windup": 0.7, "color": frost},
			{"id": &"stampede", "anim": &"boss_charge", "range": 18.0, "min_range": 6.0, "mult": 1.7, "knockback": 18.0, "poise": 60.0, "cooldown": 11.0,
				"kind": "charge", "width": 3.4, "windup": 1.0, "telegraph": "line", "speed": 13.0},
			curse(I),
			rip(I),
			{"id": &"blizzard_spiral", "anim": &"cast_channel", "range": 16.0, "mult": 0.4, "element": I, "knockback": 2.0, "poise": 6.0, "cooldown": 13.0,
				"kind": "barrage", "pattern": "spiral", "arms": 4, "duration": 3.4, "rate": 7.0, "spin": 120.0, "speed": 9.0, "reach": 26.0,
				"windup": 0.8, "color": frost, "phase": 2},
			{"id": &"whiteout", "anim": &"cast_ultimate", "range": 24.0, "mult": 1.3, "element": I, "knockback": 4.0, "poise": 14.0, "cooldown": 14.0,
				"kind": "strikes", "count": 8, "delay": 1.3, "radius": 2.4, "windup": 0.6, "phase": 3},
		],
		"xp_mult": 64.0, "drop_chance": 1.0, "gold": Vector2i(1000, 1400),
		"loot": [[&"rime_shard", 1.0, 3, 5], [&"frost_crystal", 1.0, 2, 4]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"ghoul_growl"}, "hit_material": &"flesh", "blood": Color(0.35, 0.05, 0.05),
		"corpse_time": 60.0,
		"lore": "The bastion's defenders chained the winter in its deepest cell. The winter grew fur and a hunger, and the chains rusted long before it did."})

# ------------------------------------------------------------------------------------------------ 9. the Weeping Shroud
static func shroud() -> EnemyDef:
	var wail := Color(0.55, 0.85, 1.0)
	return e(&"weeping_shroud", "The Weeping Shroud", {"family": &"undead", "role_name": "Warden of the Weeping Bastion", "model_file": "weeping_shroud.glb",
		"body_shape": &"floating", "tint": Color(1, 1, 1), "hp": 3300.0, "damage_min": 22.0, "damage_max": 32.0, "defense": 40.0, "evasion": 30.0,
		"accuracy": 80.0, "move_speed": 4.4, "weight": 6.0, "poise": 240.0, "knockback_res": 0.8, "status_res": 0.5, "affinity": D,
		"resistances": {D: 0.7, I: 0.4, WI: 0.3, LT: -0.45, F: -0.1}, "preferred_range": 10.0, "retreat_range": 5.0, "body_radius": 1.4,
		"body_height": 3.2, "model_scale": 1.0, "aggro_range": 32.0, "leash_range": 260.0, "can_be_elite": false,
		"status_immune": BOSS_IMMUNE + [&"bleeding", &"poisoned"], "sight_range": 44.0, "anim_map": {"hover": 2.2},
		"phases": [{"hp": 1.0, "name": "The Lament"}, {"hp": 0.6, "name": "Weeping"}, {"hp": 0.3, "name": "The Last Tear"}],
		"attacks": [
			{"id": &"lament", "anim": &"cast_area", "range": 18.0, "mult": 0.42, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 8.0,
				"kind": "barrage", "pattern": "radial", "count": 32, "waves": 2, "gap": 0.7, "speed": 7.5, "reach": 26.0, "windup": 0.7, "color": wail},
			{"id": &"wail_orbit", "anim": &"cast_channel", "range": 14.0, "mult": 0.4, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 11.0,
				"kind": "barrage", "pattern": "orbit", "count": 22, "waves": 4, "gap": 0.5, "curve": 70.0, "speed": 7.0, "reach": 26.0, "windup": 0.7, "color": wail},
			{"id": &"tears", "anim": &"cast_quick", "range": 24.0, "mult": 0.6, "element": I, "knockback": 2.0, "poise": 6.0, "cooldown": 9.0,
				"kind": "barrage", "pattern": "homing", "count": 7, "gap": 0.12, "homing": 100.0, "seek": 3.0, "speed": 6.5, "reach": 30.0,
				"windup": 0.6, "color": Color(0.8, 0.95, 1.0), "shot_radius": 0.45},
			{"id": &"cross_of_sorrow", "anim": &"cast_ultimate", "range": 16.0, "mult": 0.4, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 13.0,
				"kind": "barrage", "pattern": "cross", "duration": 3.4, "rate": 10.0, "spin": -50.0, "speed": 10.0, "reach": 26.0, "windup": 0.7,
				"color": wail, "phase": 2},
			curse(D, {"cooldown": 10.0, "radius": 7.5}),
			rip(D),
			{"id": &"call_the_drowned", "anim": &"boss_summon", "range": 40.0, "cooldown": 22.0, "kind": "summon", "summon": &"gloomwraith", "count": 3, "phase": 2},
		],
		"abilities": [{"id": &"drift", "kind": "teleport", "cooldown": 8.0, "range": 9.0}],
		"xp_mult": 44.0, "drop_chance": 1.0, "gold": Vector2i(600, 900),
		"loot": [[&"shadow_silk", 1.0, 2, 4], [&"champion_essence", 1.0, 2, 4]],
		"sounds": {"hurt": &"hit_bone", "death": &"boss_roar", "idle": &"cultist_chant"}, "hit_material": &"bone", "death_style": &"smoke",
		"corpse_time": 20.0,
		"lore": "Six horns, no body, and a voice that does not stop. The bastion's widows wept for so long that the weeping went on without them."})

# ------------------------------------------------------------------------------------------------ 10. Vaelgor
static func vaelgor() -> EnemyDef:
	var ember := Color(1.0, 0.35, 0.2)
	return e(&"vaelgor", "Vaelgor, the Nameless Wyrm", {"family": &"beast", "role_name": "Lord of the Throne Beneath", "model_file": "vaelgor.scn",
		"body_shape": &"quadruped", "tint": Color(1, 1, 1), "hp": 5800.0, "damage_min": 30.0, "damage_max": 44.0, "defense": 100.0, "evasion": 6.0,
		"accuracy": 80.0, "move_speed": 4.2, "weight": 20.0, "poise": 480.0, "knockback_res": 0.92, "status_res": 0.5, "affinity": F,
		"resistances": {F: 0.6, D: 0.5, E: 0.3, I: -0.3, LT: -0.2}, "preferred_range": 6.0, "body_radius": 2.2, "body_height": 4.6,
		"model_scale": 1.0, "aggro_range": 38.0, "leash_range": 260.0, "can_be_elite": false, "status_immune": BOSS_IMMUNE + [&"burning"],
		"sight_range": 48.0,
		"phases": [{"hp": 1.0, "name": "The Throne Beneath"}, {"hp": 0.66, "name": "Ash and Ember"}, {"hp": 0.33, "name": "The Name Unspoken"}],
		"attacks": [
			{"id": &"rend", "anim": &"boss_sweep", "range": 6.5, "mult": 1.4, "element": F, "knockback": 14.0, "poise": 46.0, "cooldown": 3.0, "kind": "aoe",
				"radius": 6.5, "arc": 150.0, "windup": 0.85, "telegraph": "cone", "self_centered": true},
			{"id": &"ash_breath", "anim": &"cast_channel", "hold_anim": &"cast_channel", "range": 20.0, "mult": 1.0, "element": F, "knockback": 3.0, "poise": 10.0,
				"cooldown": 12.0, "kind": "beam", "duration": 3.0, "sweep": 120.0, "windup": 0.9, "status": {&"burning": 60.0}},
			{"id": &"ember_spiral", "anim": &"cast_area", "range": 16.0, "mult": 0.42, "element": F, "knockback": 2.0, "poise": 6.0, "cooldown": 11.0,
				"kind": "barrage", "pattern": "spiral", "arms": 5, "duration": 3.0, "rate": 7.0, "spin": 110.0, "speed": 9.5, "reach": 28.0,
				"windup": 0.8, "color": ember},
			{"id": &"wingbeat", "anim": &"boss_roar", "range": 18.0, "mult": 0.5, "element": WI, "knockback": 6.0, "poise": 10.0, "cooldown": 9.0,
				"kind": "barrage", "pattern": "fan", "count": 15, "spread": 140.0, "waves": 3, "gap": 0.35, "speed": 13.0, "reach": 26.0, "windup": 0.6,
				"color": Color(0.9, 0.85, 0.8)},
			{"id": &"cinder_fall", "anim": &"cast_heavy", "range": 24.0, "mult": 1.4, "element": F, "knockback": 5.0, "poise": 16.0, "cooldown": 12.0,
				"kind": "strikes", "count": 8, "delay": 1.2, "radius": 2.6, "windup": 0.6, "phase": 2},
			{"id": &"throne_charge", "anim": &"boss_charge", "range": 20.0, "min_range": 6.0, "mult": 1.8, "knockback": 20.0, "poise": 70.0, "cooldown": 11.0,
				"kind": "charge", "width": 4.0, "windup": 1.0, "telegraph": "line", "speed": 14.0},
			curse(F, {"radius": 8.0}),
			rip(F),
			{"id": &"name_unspoken", "anim": &"cast_ultimate", "range": 16.0, "mult": 0.42, "element": D, "knockback": 2.0, "poise": 6.0, "cooldown": 12.0,
				"kind": "barrage", "pattern": "radial", "count": 36, "waves": 5, "gap": 0.45, "turn": 5.0, "speed": 8.0, "reach": 28.0,
				"windup": 1.0, "color": Color(0.7, 0.2, 1.0), "phase": 3},
			{"id": &"brood", "anim": &"boss_summon", "range": 40.0, "cooldown": 26.0, "kind": "summon", "summon": &"cinder_imp", "count": 4, "phase": 3},
		],
		"xp_mult": 72.0, "drop_chance": 1.0, "gold": Vector2i(1300, 1800),
		"loot": [[&"ember_core", 1.0, 3, 6], [&"champion_essence", 1.0, 4, 6], [&"aether_shard", 1.0, 3, 5]],
		"sounds": {"hurt": &"hit_flesh", "death": &"boss_roar", "idle": &"ghoul_growl"}, "hit_material": &"stone", "blood": Color(0.3, 0.04, 0.02),
		"corpse_time": 90.0,
		"lore": "Whoever sat on the Throne Beneath gave up their name to sit there. The last of them gave up everything else as well, and what was left grew scales."})
