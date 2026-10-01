# Beyond Heroes — maps and teleporters

The first five handcrafted maps of the vertical slice, as specified in `game_implementation.txt` (MAP 1–5). Each map is
built by a script in `game/src/world/maps/<id>.gd` (a `MapBuilder` subclass) from the Blender environment kit in
`game/assets/environment/`. Builds are deterministic (RNG seeded by the map id), so every load is identical and the
tests can make exact assertions.

Art direction follows the three reference images the user supplied (see `work/lemondev/bh-001/art_direction.md`):
room-and-corridor crypt plans, a flooded cistern lit from below by teal water against warm torchlight, and dense,
lived-in lots framed by trees and hedges.

## The chain

| # | Map (id) | Levels | Arrive at | Landmark / purpose | Leads to |
|---|----------|--------|-----------|--------------------|----------|
| 1 | Hero Sanctuary (`sanctuary`) | town | `start` (plaza), `waypoint` | Fountain plaza, waypoint terrace with knight statues, houses, market, smithy, palisade on a cliff-ringed plateau | Waypoint → Ruined Forest |
| 2 | Ruined Forest (`ruined_forest`) | 1–5 | `arrival`, `catacomb_gate` | Burnt village + graveyard, stone bridge over a misty ravine, survivors' camp, collapsed watchtower on a hill, corrupted grove, sunken catacomb gate | Gate → Catacombs; waypoint → Sanctuary |
| 3 | Ancient Catacombs (`catacombs`) | 4–8 | `entrance`, `exit` | Guard hall, sarcophagus hall, barracks, storage, ossuary loop, ritual chamber, treasure alcove, **flooded cistern** (bridge, dock, boat, arches in the water, scaffolding) | Exit → Temple (sealed until the ritual circle is found) |
| 4 | Forgotten Temple (`forgotten_temple`) | 7–10 | `arrival`, `sanctum` | Courtyard on a mountain ledge, roofless colonnaded nave, flooded chapel, ruined library, raised sanctum under the temple facade with its sealed door | Throne gate → Hollow Throne (sealed until the altar breaks the seal) |
| 5 | The Hollow Throne (`boss_arena`) | 10 | `arrival` | Bridge over a corruption abyss into a walled ring arena: 8 impact pillars, binding circle, throne dais | Return waypoint → Sanctuary (sealed until the Warden falls) |

## Teleporters

| Id | Map | Destination (map / spawn) | Lock (world flag) |
|----|-----|---------------------------|-------------------|
| `sanctuary_waypoint` | sanctuary | ruined_forest / arrival | — |
| `forest_waypoint` | ruined_forest | sanctuary / waypoint | — |
| `catacomb_gate` | ruined_forest | catacombs / entrance | — |
| `catacombs_entrance` | catacombs | ruined_forest / catacomb_gate | — |
| `catacombs_exit` | catacombs | forgotten_temple / arrival | `catacombs_ritual_seen` |
| `temple_arrival` | forgotten_temple | catacombs / exit | — |
| `temple_throne_gate` | forgotten_temple | boss_arena / arrival | `temple_seal_broken` |
| `arena_return` | boss_arena | sanctuary / waypoint | `boss_warden_defeated` |
| `cove_shrine` | westreach | sanctuary / waypoint (+ any awakened network shrine) | — |

The terrace waypoint, the forest glade waypoint and the cove shrine form a **network** (`DataIsland.NETWORK`): each
still leads to its own destination, and also to every other network shrine the hero has awakened
(`HeroData.awakened_shrines`, separate from the "discovered" `unlocked_teleporters`). With more than one destination,
activating asks where to go.

## Olivar and Wyman Outpost (bh-007, safe zones; provisional, LORE §6b)

| Map (id) | Arrive at | What is there | Leads to |
|---|---|---|---|
| Olivar (`olivar`) | `west_road`, `south_road`, `olivar_shrine`, `start` | Walled lake-trade town: plaza with the Founder's statue, Taicho's Arms Exchange, Crane's jewel stall, Angkol Les' Apothecary and alchemy table, docks and pier, the Lake Terrace waypoint | West gate → Westreach (Lake Shore Road); south gate → Wyman Outpost (Watch Road) |
| Wyman Outpost (`wyman_outpost`) | `north_road`, `west_road`, `wyman_shrine`, `bonfire`, `start` | Round stockade around the bonfire checkpoint, heroes' tents and banners, commander's lodge, Hero Register board, quartermaster, field forge, workbench, camp kettle, training yard with dummies, watchtower, Marsh Overlook above Reedwater Marsh | North gate → Olivar (Watch Road); west gate → Westreach (Fen Road) |

Both build from `SettlementBuilder` (`src/world/maps/settlement_builder.gd`): a terrain lattice with DataIsland's road
polylines flattened into it, palisade runs with gate gaps, gatehouses, corridor rails to the district boundaries,
footprint-aware greenery. New walk-through boundaries: `westreach_lake_road` ↔ `olivar_west_road`,
`olivar_watch_road` ↔ `wyman_watch_road`, `westreach_fen_road` ↔ `wyman_fen_road`. The Olivar and Wyman waypoints join
the network. The loop Old Mill → Lake Shore Road → Olivar → Watch Road → Wyman Outpost → Fen Road → Lantern Fields →
Mill Lane → Old Mill is walkable end to end.

Westreach changes: the map is 15 m wider in the east (`W` 310), the Lake Shore Road's washout is planked over and runs to
the east boundary, the Fen Road leaves Lantern Fields over the new **Fen Bridge**. Herb patches (`GatherNode`) stand in
Westreach, the Ruined Forest, Olivar and Wyman Outpost. Crafting stations (`CraftingStation`): Brannoc's anvil
(Malasugue), Angkol Les' alchemy table (Olivar), the field forge, camp workbench and camp kettle (Wyman Outpost). The
Ruined Forest's chained ogre is now the miniboss Grundle (DataMinibosses); other champions hold camps in Westreach, the
Ruined Forest and the Catacombs.

## The Guild House (bh-016)

`guild_house` (Blender kit, `tools/blender/environment/assets_guildhouse.py`) stands on the north-west lot of Malasugue at
(-11, -10) facing the plaza; the old well and Seris moved to (7.4, -10.4) / (7.6, -7.6) to make room. Its interior
`int_guildhouse` (20 x 12 m, `interior.gd:_guildhouse`) has the steward Hollis Varnay at the reception table, Bram Ostler
at the Swordfin counter (west) and Sabeth Wynn at the Lantern counter (east), and a job board on each side wall
(`GuildJobBoard`, an interactable). Both guilds' boards are read and worked through `GuildJobsWindow` / `GuildJobs`.

## Westreach and the island (provisional, LORE §6b)

`westreach` (levels 1–4) is the district below Malasugue's South Gate: Old Mill Crossroads, Lantern Fields and
Tideglass Cove, joined by the Mill Road, Field Road, Cove Steps, Coast Road and Mill Lane (two walkable loops), with the
Forest Road north into the Ruined Forest and the Lake Shore Road east (a washed-out dead end). Enemies: wolves on the
clifftop, goblins at a stolen-goods camp and raiding the farm, smugglers at Saltmouth Cave, two of the dead on the
Forest Road. The mill, the gate fork and the cove are safe.

Maps join by **walk-through boundaries** (`MapExit`, `MapBuilder.exit_zone`), which travel through the loading screen:

| Exit | Map | Leads to | Condition |
|------|-----|----------|-----------|
| `sanctuary_south_gate` | sanctuary (beyond the gate) | westreach / town_gate | `south_gate_open` (Captain Hald) |
| `westreach_south_gate` | westreach (below the gate) | sanctuary / gate | — |
| `westreach_forest_road` | westreach (north edge) | ruined_forest / south_road | — |
| `forest_south_road` | ruined_forest (cut in the south rim) | westreach / forest_road | — |

**One source of road data.** `src/data/data_island.gd` holds every named place, every road as an authored polyline in
its map's local metres, and every link (boundary, door, shrine, dungeon gate). Westreach flattens its road beds and
lays its cobbles from those polylines; the M map draws them; `RoutePlanner` (`src/world/island/route_planner.gd`)
plans over them (Roads / Shortest walk / Waypoints), and `Routes` (autoload) tracks the chosen route for the HUD.
The atlas art (`assets/ui/atlas/salmonan_atlas.png`, generated by `tools/ui_art/salmonan_atlas.py`) has no text or
roads baked in; charted surface maps share one scale (0.7 m per atlas pixel), so drawn and walked lengths agree.

`Teleporter` (`src/world/teleporter.gd`) supports destination map + spawn, destination name, locked state, unlock
condition, transition (rune charge-up, beam, flash), loading screen (`src/ui/loading_screen.gd`), sound (hum, charge,
whoosh) and VFX (motes, light). Standing on a dais registers it on the hero (`unlocked_teleporters`, for the world-map
UI) and shows the travel prompt; `interact` (R) travels. Locked daises stay dim and show their hint.

World flags are set by `FlagTrigger` volumes (walk into them): `catacombs_ritual_seen` (ritual circle, 120 XP) and
`temple_seal_broken` (altar of the first oath, 400 XP; also dissolves the violet seal on the temple door). Nodes
registered with `MapBuilder.hide_when(node, flag)` disappear once the flag is set, including on later loads.
`boss_warden_defeated` is reserved for the boss encounter.

## Zarael Island (bh-029)

Reached by the **Sunwake** from Wyman Outpost's Marsh Jetty once Kethrax has fallen (`zr_ship`, spawn `jetty` on
Wyman, spawn `pier` at Agdao). The island has its own atlas (`DataIsland.ZARAEL_*`, 1 m per atlas pixel,
`tools/ui_art/bh029_atlas.py`); the M map shows whichever island the hero stands on. Every Zarael glow is pure white.

| Map (id) | Levels | Size (m) | Landmarks | Exits |
|---|---|---|---|---|
| Agdao (`agdao`) | town | ~170 x 160 | Pier and the Sunwake, harbour ward, Wire Market, five terraces with grand stairs, lifts and roof footbridges, council hall, the Crown of Steps (Wirekeeper at its top), waypoint `agdao_shrine` | East gate → the Coilwood |
| The Coilwood (`zr_coilwood`) | 30–36 | ~280 x 200 | Overgrown shrine (waypoint), aqueduct fork, three relay pylons, Kharvenn camp, Jade Sepulchre gate | West → Agdao, east → the Barrens |
| The Glasswire Barrens (`zr_barrens`) | 36–42 | ~260 x 200 | Survivors' camp (waypoint), the fallen colossus, Obsidian Engine and Veinworks gates | West → the Coilwood, north → the Bridge |
| The Bridge of Death (`bridge_of_death`) | 42–46 | ~80 x 330 | Gatehouses, three ward pylon pairs (one per Vault), Varrogh's platform | South → the Barrens, north → the Citadel (after Varrogh) |
| The Heart Citadel (`zr_citadel`) | 46–52 | ~200 x 170 | Siege camp, avenue, the Dawn Engine and the Leash-Abbot's arena | South → the Bridge |

Vaults (generated floors, `DataDungeonsZarael`): the Jade Sepulchre (33–40, gate in the Coilwood), the Obsidian Engine
(39–46) and the Veinworks (45–53) (gates in the Barrens).

## Gameplay markers for later systems

- `enemy_zone` markers (group `enemy_zone`): position, radius, archetype list, pack size, elite chance — ready for the
  enemy spawner. Every combat room/clearing has one.
- `boss_spawn` (group) and eight `arena_pillar` nodes in the Hollow Throne for the Warden's charge-into-pillar stun.
- Breakable crates, barrels, urns and small statues (`Breakable`): pre-fractured Blender fragments, capped debris speed,
  debris on its own physics layer and despawned, so impacts cannot chain.

## Authoring conventions (`MapBuilder`)

- Metres, Y up. The isometric camera looks from +Z (south), so kit fronts (doors, sconces, facades) face +Z.
- Architecture snaps to a 4 m wall grid. `room()` lays floor tiles, full walls on north/east/west, a **low cutaway wall on
  the south side** (so interiors stay readable from above, as in the cistern cutaway reference) and quoined corner pillars.
  Segment indices count from each side's north or west end. `corridor()` does the same for 4 m passages.
- `terrain()` sculpts a heightfield (mesh + `HeightMapShape3D`) with a splat shader; `water()`, `mist()`, `shaft()`,
  `cliff_ring()`, `floor_disc()` add atmosphere and framing; `torch()`, `brazier()`, `campfire()`, `candles()`,
  `lamp_post()` place kit pieces with flickering lights at their sockets.
- Small decoration is batched into one `MultiMeshInstance3D` per asset (`decor()` / `scatter()`).
- Colliding geometry lives under the map's `NavigationRegion3D`; the navmesh is baked when the map loads.

## Running and checking

```bash
# play from a given map (temporary explorer pawn until the Phase 2 player controller lands)
godot --path game -- --map=catacombs --spawn=entrance
# unit + integration tests (includes tests/unit/test_maps.gd)
godot --headless --path game res://tests/run_tests.tscn
# island data, routes, the South Gate, waypoint network and save v4 (suite subset)
godot --headless --path game res://tests/run_tests.tscn -- --only=test_island,test_maps
# the Salmonan evidence run: real game, M map, a route walked by steering input through the gate (screenshots + report)
godot --path game --resolution 1920x1080 res://tests/tools/capture_salmonan.tscn -- --class=knight --slot=97 --out=<dir>
# build + navmesh bake time per map
godot --headless --path game res://tests/tools/time_maps.tscn -- --maps=sanctuary,westreach,ruined_forest
# end-to-end playtest: walks the whole chain with physics and uses every teleporter
godot --headless --path game res://tests/tools/playtest.tscn
# screenshots of every map view, and top-down navmesh images
godot --path game --resolution 1600x900 res://tests/tools/capture_maps.tscn -- --out=<dir>
godot --headless --path game res://tests/tools/nav_maps.tscn -- --out=<dir>
```

The environment kit regenerates from `tools/blender/environment/` (see its README).
