class_name DataZarael
## bh-029: Zarael Island, the corrupted (docs/LORE.md §11) — one source for its maps, the ship, the quest flags and the
## spots the map builders, the quests (Objectives), the NPCs and the routes (DataIsland) share. Map-local metres, Y up,
## +Z south (toward the camera), as every MapBuilder.
##
## The ship: after Kethrax falls (`boss_kethrax_defeated`) Agdao's ship lies at Wyman Outpost's Marsh Jetty. Old saves
## that already have the flag see it the moment they load Wyman. It sails between Wyman (spawn `jetty`) and Agdao's
## pier (spawn `pier`). The first landing plays Terax's welcome (cutscene `terax_welcome`, flag `zr_terax_met`).

const MAPS: Array[StringName] = [&"agdao", &"zr_coilwood", &"zr_barrens", &"bridge_of_death", &"zr_citadel"]
const DUNGEONS: Array[StringName] = [&"jade_sepulchre", &"obsidian_engine", &"veinworks"]

## The flag that brings the ship (Kethrax's fall) and the quest flags, in story order.
const SHIP_FLAG := &"boss_kethrax_defeated"
const F_SAILED := &"zr_ship_sailed"
const F_TERAX := &"zr_terax_met"
const F_WIREKEEPER := &"zr_wirekeeper_met"
const F_RELAYS := &"zr_relays_cut"
const RELAY_FLAGS: Array[StringName] = [&"zr_relay_1", &"zr_relay_2", &"zr_relay_3"]
## Each Vault counts as cleared when its lord falls the first time (DataDungeons.cleared_flag: dg_<id>_cleared).
const VAULT_FLAGS := {&"jade_sepulchre": &"dg_jade_sepulchre_cleared", &"obsidian_engine": &"dg_obsidian_engine_cleared",
	&"veinworks": &"dg_veinworks_cleared"}
const F_BRIDGE := &"boss_deathspan_defeated"
const F_ABBOT := &"boss_leash_abbot_defeated"
const F_RESTORED := &"zr_heartwire_restored"
## Set once the hero has been told the ship is waiting (a toast on Kethrax's fall or on loading an old save).
const F_SHIP_TOLD := &"zr_ship_told"

# ------------------------------------------------------------------------------------------------ Wyman Outpost
## The Marsh Jetty: a small gate in the south-east of the stockade (JETTY_GATE_DEG round the camp's centre), planks
## down to the bank, then a jetty east over Reedwater Marsh. The ship lies at its end once Kethrax has fallen.
const WY_JETTY_GATE_DEG := 35.0
const WY_WALK := [Vector2(25.4, 17.8), Vector2(29.5, 21.5), Vector2(35.0, 26.0)]   # stockade gate → jetty root
const WY_JETTY_ROOT := Vector2(35.0, 26.0)
const WY_JETTY_END := Vector2(55.0, 26.0)
const WY_SHIP := Vector3(61.0, 0.0, 26.0)           # the ship's waterline centre (bow toward −Z)
const WY_SPAWN := Vector3(41.0, 0.0, 26.0)          # spawn `jetty` (on the jetty, facing the camp)
const WY_CAPTAIN := Vector3(53.0, 0.0, 24.8)        # Captain Ilsa Rhondar, by the gangplank

# ------------------------------------------------------------------------------------------------ Agdao
const AG_PIER_X := -20.0                            # the pier runs north-south on this line
const AG_PIER_Z := Vector2(44.0, 76.0)              # from the harbour wall to the pier end
const AG_DECK_Y := 1.6                              # the pier and harbour quay deck height
const AG_SHIP := Vector3(-9.5, 0.0, 64.0)           # the ship's waterline centre, moored east of the pier
const AG_SPAWN := Vector3(-20.0, 0.0, 66.0)         # spawn `pier` (where the gangplank meets the pier)
const AG_TERAX := Vector3(-20.0, 0.0, 47.0)         # Terax waits at the head of the pier
const AG_SHRINE := Vector2(26.0, 18.0)              # the waypoint on the Market Terrace
const AG_WIREKEEPER := Vector3(0.0, 0.0, -70.0)     # Wirekeeper Halvessa Orn, at the top of the Crown of Steps
const AG_GATE := Vector2(80.0, -26.0)               # the Coilwood Gate (east side, upper town)
const AG_GATE_SPAWN := Vector3(72.0, 0.0, -26.0)    # spawn `coil_gate` (inside the gate, facing west)

# ------------------------------------------------------------------------------------------------ the Coilwood
const CW_WEST := Vector3(-132.0, 0.0, 30.0)         # spawn `agdao_road`
const CW_EAST := Vector3(132.0, 0.0, 8.0)           # spawn `barrens_road`
const CW_SHRINE := Vector2(-108.0, 18.0)            # waypoint in the ruined shrine near the Agdao road
const CW_RELAYS := [Vector2(-58.0, -42.0), Vector2(18.0, 52.0), Vector2(66.0, -28.0)]
const CW_CAMP := Vector2(28.0, -58.0)               # the Kharvenn camp

# ------------------------------------------------------------------------------------------------ the Glasswire Barrens
const GB_WEST := Vector3(-124.0, 0.0, 10.0)         # spawn `coil_road`
const GB_NORTH := Vector3(30.0, 0.0, -92.0)         # spawn `bridge_road`
const GB_CAMP := Vector2(-40.0, 30.0)               # the survivors' camp with its waypoint
const GB_COLOSSUS := Vector2(48.0, -28.0)           # the fallen colossus

# ------------------------------------------------------------------------------------------------ the Bridge of Death
const BR_SOUTH := Vector3(0.0, 0.0, 148.0)          # spawn `barrens_road` (the south approach)
const BR_NORTH := Vector3(0.0, 0.0, -156.0)         # spawn `citadel_road` (north end, inside the gatehouse)
const BR_DECK_Z := Vector2(132.0, -132.0)           # the span: south gatehouse to the north platform
const BR_PYLONS := {&"jade_sepulchre": 84.0, &"obsidian_engine": 4.0, &"veinworks": -76.0}   # z of each ward pylon pair
const BR_BOSS := Vector3(0.0, 0.0, -118.0)          # Varrogh's platform
const BR_GATE_N := -146.0                           # z of the north gatehouse (sealed until Varrogh falls)

# ------------------------------------------------------------------------------------------------ the Heart Citadel
const HC_SOUTH := Vector3(0.0, 0.0, 78.0)           # spawn `bridge_road`
const HC_ENGINE := Vector3(0.0, 0.0, -40.0)         # the Dawn Engine
const HC_ABBOT := Vector3(0.0, 0.0, -18.0)          # the Leash-Abbot's spawn, in front of the Engine
const HC_ARENA_R := 26.0

# ------------------------------------------------------------------------------------------------ helpers

static func is_zarael_map(map_id: StringName) -> bool:
	if MAPS.has(map_id) or String(map_id).begins_with("int_agdao"):
		return true
	var d := DataDungeons.parse(map_id)
	return DUNGEONS.has(d[0])

static func has(hero: HeroData, flag: StringName) -> bool:
	return hero != null and bool(hero.world_flags.get(flag, false))

## The ship lies at Wyman once Kethrax has fallen.
static func ship_ready(hero: HeroData) -> bool:
	return has(hero, SHIP_FLAG)

static func relays_cut(hero: HeroData) -> int:
	var n := 0
	for f in RELAY_FLAGS:
		if has(hero, f):
			n += 1
	return n

static func vaults_cleared(hero: HeroData) -> int:
	var n := 0
	for d in VAULT_FLAGS:
		if has(hero, VAULT_FLAGS[d]):
			n += 1
	return n

## The Heartwire's state for a hero: "corrupt" until the Dawn Engine is restored, then "restored".
static func wire_state(hero: HeroData) -> String:
	return "restored" if has(hero, F_RESTORED) else "corrupt"
