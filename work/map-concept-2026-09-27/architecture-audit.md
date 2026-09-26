# Salmonan map architecture audit

Date: 2026-09-27. Scope: read-only source audit for the larger-island concept. This report does not claim a runtime playtest; the lead agent owns live play and visual evidence. No game files were changed by this audit.

## Finding

The current **world progression and atlas are a chain**, while some individual spaces already contain worthwhile branches. A much larger island needs a connected geography and route data shared by terrain, signs, the atlas and directions. Enlarging the current forest rectangle or painting more circles on the existing atlas would preserve the actual problem.

## Verified implementation

All paths below are relative to `A:\Python\beyond-heroes`.

| Location | Current behavior | Consequence |
|---|---|---|
| `game/src/data/data_maps.gd:14` | Five exterior/dungeon map definitions: Malasugue (`sanctuary`), Ruined Forest, Ancient Catacombs, Forgotten Temple, Hollow Throne. Eight town interiors are appended. | Preserve these IDs for saves; new island districts can be added without rewriting the legacy story. |
| `game/src/core/defs/map_def.gd:17` | One normalized `world_map_pos` per map and a `waypoint` boolean; no island boundary, roads, POIs, region transform, elevation/floor or graph. | A single point cannot express a district, surface entrance or underground network. |
| `game/src/ui/windows/world_map_window.gd:14` | Hardcoded `ORDER` of the five maps. `_draw_map()` draws roads between successive list entries. `_on_input()` only handles hover. | M is already present, but there is no destination selection, search, route planner, route line, zoom/pan or travel selection. The chart depicts chronology as geography. |
| `game/src/autoload/input_setup.gd:12`, `game/src/ui/ui_root.gd:18` | M and Tab map to `world_map`; `UIRoot` toggles the window, whose nominal size is 1500×880. | Extend the existing action, with responsive layouts, rather than introducing a duplicate M handler. |
| `game/src/ui/ui_root.gd:111`, `game/src/actors/player/player.gd:970` | Opening a window blocks gameplay input through `Game.ui_blocking`; this method does not itself pause the tree. | Planning during danger needs an explicit tested rule. Input blocking alone can leave the hero vulnerable. |
| `game/src/world/maps/ruined_forest.gd:4` | Its stated design is “West → east along one winding road.” `ROAD` runs from x=-66 to x=66; tower and camp paths are short branches. Bounds are 144×96 m in XZ. | There are side encounters, but one crossing and one forward destination dominate the macro journey. |
| `game/src/world/maps/catacombs.gd:8` | Guard Hall → Sarcophagus Hall OR Barracks → Storage → Ossuary → Ritual Chamber; eastern Flooded Cistern and Treasure Alcove. | Preserve the existing loop and room identity. Do not describe every map as a corridor. |
| `game/src/world/maps/sanctuary.gd:57` | Malasugue bounds are 84×84 m. Terrace waypoint goes to forest. Barred South Gate and enterable guild/house spaces are already built. | Keep the recognizable town and guild arrangements. Add an explicit gate-opening story beat before allowing surface travel through the barred gate. |
| `game/src/world/teleporter.gd:12` | Each teleporter has exactly one destination map/spawn. Discovery records its ID; activation charges then calls `Game.travel`. | Existing teleporters are paired transitions, not a selectable discovered-shrine network. |
| `game/src/world/teleporter.gd:142` | `discover()` records the teleporter even when it is locked; lock checks happen separately. | `unlocked_teleporters` is historically closer to “discovered teleporters.” Do not equate presence in this dictionary with permission to travel. |
| `game/src/autoload/game.gd:140` | `load_map()` builds the entire destination, removes the previous scene, synchronously bakes navigation, populates enemies/NPCs and reparents the player. | It supports bounded districts now, not seamless large-world streaming. A single giant scene would amplify bake and spawn cost. |
| `game/src/world/map_builder.gd:46` | One NavigationRegion3D per MapRoot, 0.25 m nav cell, 0.5 m agent radius, 2 m height, 0.5 m climb, 40° slope. `bake_navigation()` calls non-threaded bake and forces server synchronization. | Author routes against actual traversal limits. Prebaked/bounded navigation is necessary before making a large seamless island. |
| `game/src/world/spawner.gd:12` | Populates a fresh map from all enemy-zone markers; deterministic seed uses map/zone identities. | Bigger loaded geography means more active enemies unless activation/state ownership is changed. |
| `game/src/ui/hud/minimap.gd:28` | Live top-down orthographic camera, 26 m radius, geometry updated every 0.2 s. Marker pass scans scene groups. | Add route and destination overlays using the existing world-to-map transform; do not substitute the illustrated island atlas for the useful local minimap. |
| `game/src/core/objectives.gd:6` | Main objective is the first unfinished item in one flag-driven chain. | Keep the main story chain, but add independent optional destination records and activities; do not require completing every district in a sequence. |
| `game/src/core/hero_data.gd:20`, `game/src/core/hero_data.gd:304` | Saves discovered map IDs, teleporter IDs, world flags, current map and named spawn. No exact player position or POI discovery list. | New navigation/discovery data needs migration. Current resume restarts at the remembered named spawn, which is costly on a larger island. |
| `game/src/autoload/save_system.gd:6` | Save version 3, stepwise v1→v2→v3 migrations. | Add an explicit v3→v4 migration with fixtures rather than silently interpreting old IDs as new unlocks. |

## Canon constraints

`docs/LORE.md` is the authority. Jre has four major islands. Salmonan is the green-cliff, fishing-cove, old-forest island; Malasugue is on its **west coast**, on a cliff plateau. The Oros sleeps beneath it; it is not a normal enemy or an exposed moving creature. The Holy War remains impending. Sanctuary Terrace is the north end of Malasugue. Swordfin Hall is east of the plaza; Lantern House is west. Their colors remain sea-blue/silver and violet/gold; Aether is pale cyan, not interchangeable generic purple magic.

Keep Ruined Forest, the Catacombs, Forgotten Temple, Hollow Throne, Morthar and their world flags. The surface atlas should show the Catacombs as an entrance beneath the drowned chapel, with a separate underground layer/inset. The Hollow Throne should read as a destination belonging to the temple sequence rather than a fifth freestanding island town. All additional district, road and settlement names are **provisional design proposals** until entered into the lore bible. Do not replace author canon or invent a real-world cultural theme.

## Recommended data and navigation design

Introduce data resources instead of making the atlas image authoritative. Proposed names below are implementation directives, not existing files.

1. `IslandDef`: island ID, title, artwork reference, world/map coordinate transform, coastline and district polygons, north orientation, atlas bounds and layers.
2. `PlaceDef`: stable POI ID, display name, kind (town/service/shrine/entrance/landmark), map ID, local XZ position, floor, island position, discovery rule, required flags and optional destination spawn. Separate named surface entrances from underground interior locations.
3. `RoadEdgeDef`: stable edge ID, endpoint junctions, authored polyline, width, road/trail type, length, district transitions, traversal/lock requirements, baseline danger and encounter IDs. Road geometry, cartography and sign destinations reference the same edge IDs.
4. `TravelLinkDef`: explicit directed edge between named spawn endpoints with mode `walk`, `door`, `shrine` or another deliberately authored mode. Record discovery, lock and arrival requirements. Never infer a connection from the order of maps in a list.
5. `RoutePlan`: selected destination, ordered legs, active leg, total walking distance, estimated walking time, required transition and unavailable reason. The atlas and HUD consume one service, not duplicate planner logic.

Use a high-level weighted graph for inter-district planning and existing navmesh queries for the current walking leg. Road-preferring graph routes should deliver believable roads; navmesh paths validate collision-free connectors from the actual player position to those road legs. Do not draw a straight cyan line through cliffs just because two icons are close. Underground floors and coastlines must not collapse onto a shared 2D shortest path.

Routing modes: **Roads** (default), **Shortest walk**, and **Use awakened waypoints**. Time estimate derives from measured length and the hero's effective movement speed, excludes combat, and says “walking estimate.” Hazard changes can influence route cost; do not promise a perfectly “safe” route through uncontrolled enemy space. A locked destination shows its condition. A known destination without a route says “No known route.” New map discovery must not reveal every secret chest or unvisited shrine automatically.

Directions are guidance, not mandatory autoplay: next turn/landmark, remaining distance, destination pointer at the minimap edge, subtle local route hints, and a **Clear route** control. Replan when sufficiently off course, after a transition or after flags change, with throttling and hysteresis so the arrow does not flicker between routes. On entering a building, keep the destination through the correct door leg. Shrine travel is offered at a shrine to awakened eligible shrines; clicking the atlas sets a route unless the travel conditions explicitly permit immediate travel.

## Larger-island delivery sequence

First validate a looped exterior **district** around recognizable Malasugue, retaining named interior maps. The player should have at least three legible surface destinations and two reconnecting travel loops, with different landmark views and encounter/reward character. Preserve the legacy shrine link so existing saves and new players can still reach Ruined Forest. Opening a road out of town requires story/collision changes as a single feature.

Build additional bounded exterior districts connected by walk-through boundary transitions using `Game.travel` or a dedicated transition wrapper. A coherent illustrated island atlas can represent these as continuous geography while the runtime has explicit loading boundaries. This is a practical first milestone and must be described honestly. Do not claim it is seamless.

Before a seamless phase, separate persistent island state from scene ownership. Introduce chunk activation, stable encounter/container IDs, local navigation regions with validated seams, environment ownership, and a player/camera/companion parent independent of any unloading chunk. Current `MapRoot` owns environment, bounds and the player; `FX.world`, NPC population and respawn also assume one active map. Those assumptions must be addressed together. Use measured budgets on the target machine, baked navigation or asynchronously prepared regions, and staged activation. No full-island synchronous rebake during movement. Loading/unloading cannot reroll loot, resurrect cleared special encounters, strand Tempos or destroy the active route.

Scale should follow walking time and encounter spacing, not a marketing number. Prototype density first: meaningful fork or landmark roughly every 30–60 seconds at base walking speed, a short local loop in 2–4 minutes without combat, longer cross-district walks supported by awakened shrines. Treat these as initial design targets to validate, not measurements of the existing build. Avoid filling increased area with repeated wolves and empty jogging.

## Parallel implementation ownership

Agent A: island/place/road/travel resources and route service; migrate saves; freeze IDs and coordinate contracts before consumers build on them.

Agent B: Malasugue-adjacent terrain and surface road loops; shared edge IDs; sight lines, signs, shrine approaches and collision/nav validation. Preserve recognizable town structures and canon.

Agent C: M atlas, layered art, search/filter/selection panel and HUD directions. Use Agent A's service. Surface labels at readable sizes, icons with shape plus color, current-player marker, route contrast, zoom-dependent label density and keyboard navigation. No tiny-uppercase essential text.

Agent D: integration/QA: save fixtures, reachability, off-route tests, sign/road/art consistency, actual fresh-save playthrough and measured loading/frame time. Findings need screenshots, route IDs and reproducible steps.

Art generation is a separate deliverable from correctness: atlas artwork establishes coastline/landmark style; road polylines, icons, names, current position and route remain native UI layers. Ship the clean artwork plus overlay sources. Never bake changing player pointers, route lengths or interactive text into the only image.

## Acceptance gates

- **Topology:** the playable exterior graph has at least two independent cycles and three early reachable named destinations. A player can choose a loop and return by another road. Optional branches have distinct play/reward reasons. The main story can stay ordered.
- **Geographic truth:** every displayed traversable road follows an actual route; every shrine/door resolves to a valid map/spawn. Surface and dungeon floors are separated. Malasugue remains west-coast and guild locations stay consistent.
- **Navigation:** every road junction, approach, bridge and boundary is reachable under the configured 0.5 m radius/40° slope navigation limits. Test actual enemy and companion movement too; nav polygons alone are insufficient.
- **M interface:** open/close works with M and Escape; no input leaks to attacks or shrine activation; search selects a location, Directions produces a valid route, Clear route removes it; zoom/pan retain a useful view; essentials remain readable at 1280×720 and 1920×1080.
- **Directions:** follow a town→junction→shrine→different-map→entrance route by foot; deliberately take a wrong turn, enter/leave an interior and toggle a lock flag. The next instruction and line update correctly. Locked/unreachable destinations never produce false success or paths across sea/cliffs.
- **Discovery and travel:** discovered-but-locked legacy teleporters remain locked. A new arrival does not awaken unrelated shrines. Shrine menu presents only eligible targets and a destination preview; arrivals do not immediately retrigger return travel.
- **Persistence:** load a v3 save in each legacy map and a town interior; preserve guild, tier, world flags, equipment and Tempos. New discovery/route data round-trips. Missing/removed POIs fail gracefully. Resume/respawn goes to an authored safe point without losing a long island journey unexpectedly.
- **Performance:** record baseline and candidate on the same machine, resolution and route. Report scene load, worst/95th-percentile frame time, memory, draw calls and active enemies. Set numeric budgets from this baseline before art expansion; no made-up claim that a larger island is “optimized.”
- **Play evidence:** fresh-save footage through both early loops, screenshots at every decision junction and atlas screenshots with the matching route; list observed issues separately from code inferences. A decorative overhead render alone does not pass.

Reuse `game/tests/unit/test_maps.gd` for map/spawn validity, locks, deterministic builds and critical reachability. Expand its hardcoded map list and chain assertions to cover the authored graph while preserving the legacy story path. `game/tests/tools/nav_maps.gd` already creates navmesh PNGs; use these alongside art overheads to catch beautiful but disconnected terrain.
