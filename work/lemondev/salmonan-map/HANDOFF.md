# Salmonan map milestone — handoff

Run: `salmonan-map`, 27 September 2026. Source brief: `work/map-concept-2026-09-27/` (README, WORLD-DESIGN, architecture
audit, island graph). Engine: Godot 4.7.2, Forward+, Windows 10, RTX 4060. Branch: `main`, **uncommitted working tree**.

## Status

**IMPLEMENTED — UNVERIFIED.** The milestone is built and exercised in the real game with scripted input. Component
tests and the integration checks listed below pass. There was no independent blind critic review against a benchmark
(no subagent was run), no 3840×2160 UI check, and no manual human playthrough. See *Unverified*.

## Scope (the concept's "first milestone")

- A looped exterior district next to Malasugue, instead of a bigger forest rectangle.
- The island data model and a single route service shared by terrain, signs, the atlas and the HUD.
- The M atlas with search and directions.
- In-play directions.
- The shrine network.
- Save v4.

**Out of scope, kept as proposals:**
- Watcher's Rise, the Drowned Chapel surface entrance, the lake circuit and Reedwater Marsh.
- A second forest crossing.
- Seamless streaming.
- In-world ground hints for the route.

## What changed and where

| Area | Files |
|---|---|
| New district **Westreach**: Old Mill Crossroads (turning water wheel, stone bridge, four-armed signpost), Lantern Fields (terraced crop plots, farmstead, lanterns), Tideglass Cove (beach, pier, boats, shrine), Saltmouth Cave, Coast Road clifftops, switchback Cove Steps, washed-out Lake Shore Road; goblins, wolves, smugglers, 2 hollow soldiers; mill, gate fork and cove are safe | `game/src/world/maps/westreach.gd`, `data_maps.gd` |
| Island data: places, roads (authored polylines in each map's local metres), links (boundary, door, shrine, dungeon), network shrines, atlas transform (0.7 m/px) | `game/src/data/data_island.gd` |
| Route planner (Roads / Shortest walk / Waypoints; lock reasons; start from the hero's real position; walking-only distances) | `game/src/world/island/route_planner.gd` |
| Tracked route service (instruction, remaining distance, guide point, off-route replan with 10 m / 1 s / 0.5 s throttle, arrival, link triggers, discovering hidden places) | `game/src/autoload/routes.gd` (new autoload `Routes`) |
| South Gate story beat: Captain Hald's "About the south road..." dialogue sets `south_gate_open`; the bar and gate lift, the collision goes, and the road runs out of the gate | `data_npcs.gd`, `sanctuary.gd`, `map_root.gd` (hidden colliders stop colliding), `game.gd` (flags apply before the navmesh bake) |
| Walk-through map boundaries (gate road, Forest Road) | `game/src/world/map_exit.gd`, `MapBuilder.exit_zone/signpost`, `sign_labels.gd` |
| Forest Road south exit from the burnt village | `ruined_forest.gd` |
| Waypoint network (discovered ≠ awakened; chooser when a shrine has several destinations) | `teleporter.gd`, `ui_root.gd` |
| M map rewrite: clean atlas base, mist shader, native roads/markers/labels, true player position and heading, search, sidebar, modes, Directions / Set route / Clear route, Island / Local / Underground, zoom/pan, legend, true scale bar, world paused while open | `world_map_window.gd`, `ui/widgets/atlas_view.gd`, `ui_root.gd` |
| HUD directions panel + route on the minimap (also fixes the `!is_inside_tree()` error in `minimap._draw_markers`) | `ui/hud/directions_panel.gd`, `hud.gd`, `minimap.gd` |
| Atlas art generator (no text baked in) | `tools/ui_art/salmonan_atlas.py` → `game/assets/ui/atlas/` |
| Save v4 (awakened shrines, found places, tracked route; v3→v4 migration) | `hero_data.gd`, `save_system.gd` |
| Docs | `docs/LORE.md` §6 South Gate + new §6b (provisional), `docs/MAPS.md` |
| Tests and tools | `tests/unit/test_island.gd` (new), `test_maps.gd` (+westreach), `run_tests.gd` (`--only=`), `tools/capture_salmonan.*`, `tools/time_maps.*` |

## Setup and launch

Use your normal Godot 4.7.2 editor and project. To play from the south gate with a fresh knight, use a spare slot;
slot 97 is what the evidence runs used:

```bash
godot --path game -- --class=knight --slot=97
```

In play:
- Talk to Captain Hald at the South Gate and choose "About the south road...", then "Open the gate".
- **M** opens the map. Search with **F**, zoom with the mouse wheel, pan by dragging, **C** centres on you.
- Pick a place, then **Directions** (preview), **Set route** (track) or **Clear route**.
- **M** or **Esc** closes the map.

## Gate results

| Gate | Result |
|---|---|
| Unit and integration tests | `godot --headless --path game res://tests/run_tests.tscn`: **5,265 checks, 0 failures** (baseline before this work: 4,717 / 0). `test_island`: 522 checks. `test_maps` with Westreach: 406 checks. |
| Roads are real | Every charted road is sampled every 5 m and stays on the navmesh, and each road's endpoints connect by navmesh path with a walked length within 1.35× of the road. This caught and fixed a real disconnection: the mill bridge was 0.9 m below the road bed, and stray stream rails were blocking the bridge. |
| Topology | Walkable exterior (roads + boundaries): ≥ 2 independent cycles, 1 connected component. With the gate open, Old Mill, Lantern Fields and Tideglass Cove are each reachable on foot from the plaza with no transfer, at 60–450 m. |
| Locks | A barred gate is never routed through. The temple and throne report their locks ("…ritual chamber…", "…seal…"). An unknown destination fails. A locked dungeon dais is discovered but never awakened. |
| Save | A v3 fixture migrates to v4 with only the two legacy waypoints awakened. Shrines, found places and the route round-trip through JSON. Removed ids are dropped without error. |
| In-game run (real boot, knight, slot 97, scripted input) | Town → Lantern Fields through the South Gate boundary: **arrived, 171 m walked in 32.3 s**. Fields → Tideglass Cove along the Coast Road: **arrived, 215 m in 40.4 s**. Wrong turn (Coast Road instead of Mill Lane): 2 replans, instruction changed once ("Follow Mill Lane…" → "Head along Coast Road to Lantern Fields"), no flicker. M opens, pauses and closes, and unpauses on close. |
| Readability | Checked at 1920×1080 (1920×1040 window) and 1280×720. Essential text (place labels, steps, summary, lock reason, HUD instruction) is 24 logical px, about 16 px at 720p. Secondary notes and hints are 18–19 logical px (about 12–13 px at 720p). |
| Blind benchmark review | **Not run** (no independent critic). The concept mock `work/map-concept-2026-09-27/images/map-directions-ui-v1.png` is the design target, not a commercial benchmark. |

## Performance (measured, not a budget sign-off)

- **Environment:** RTX 4060, 1920×1040 window, VSync on, knight walking the route with god mode, `capture_salmonan`.
- **Westreach, 4,244 frames:** average 16.74 ms, p95 16.67 ms, worst 111.3 ms (a single hitch).
- **Malasugue, 136 frames:** average 17.4 ms, p95 16.67 ms, worst 108.5 ms.
- **Gate transition:** 5.36 s, including the loading screen's fades.
- **Build + navmesh bake (headless `time_maps`):**

| Map | Build | Bake |
|---|---|---|
| Westreach | 1.7–2.2 s | 0.5–0.8 s |
| Malasugue | 1.0 s | 0.16 s |
| Ruined Forest | 0.7 s | 0.1–0.2 s |

- **Westreach counts:** 52 omni lights (3 shadowed), about 5,080 navmesh polygons.
- The 108–111 ms worst frames are not yet attributed; first-use shader compilation is the likely cause but not verified.

## Evidence

- `work/lemondev/salmonan-map/evidence/final-1080p/`: 16 screenshots and `report.json` (plans, walks, wrong turn, frame times).
- `evidence/final-720p/`: the map at 1280×720.
- `evidence/pass1/`: district renders from the map capture tool.
- `evidence/nav/`: the Westreach navmesh image.

## Unverified items and the remaining largest gap

1. **Blind comparison.** No context-isolated critic has compared the atlas or district against a benchmark. This is the largest remaining gap for acceptance.
2. **No human playthrough.**
   - **Combat:** god mode was on in the evidence runs, and encounter difficulty for level 1–3 heroes in Westreach is untested.
   - **Tempo companions:** not tested on the new roads.
   - **Controller:** no controller or keyboard-only focus pass has been done on the map.
3. **UI at 3840×2160:** not inspected.
4. **Barred-gate bypass (design question):** with the South Gate still barred, Westreach is reachable through the waypoint, the forest and the Forest Road. The planner uses that route, which is correct, but it is a design choice to confirm.
5. **Art quality:** the atlas base is procedural. It is clean and consistent with the data, but less painterly than the concept painting.
6. **Night darkness:** Westreach is dark at night like the other exterior maps.

## Pass count

- **Build and fix passes:** 5 on this component set. Each pass captured its evidence, found the single largest defect and fixed it:
  1. The guide stopped at the gate.
  2. Labels were cluttered.
  3. The bridge navmesh was disconnected.
  4. The wrong-turn test was invalid.
  5. Text below 16 px at 720p.
- **Critic passes:** 0.
- **Next action:** run an independent review of `final-1080p` and `final-720p` against the concept mock, then a human playthrough without god mode, combat included.
