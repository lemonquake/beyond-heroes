# Current-build playtest and map evidence

Review date: 27 September 2026. Game: Beyond Heroes. No production code was changed for this review.

## Method and limits

I ran the actual Godot 4.7.2 runtime and rendered its native viewport with Vulkan Forward+ on the NVIDIA RTX 4060. A dedicated test harness boots the real Main scene, creates the real knight Player, presses movement actions through the existing input system, and injects an M key event through `Input.parse_input_event`. This is an instrumented runtime playtest, not a manual mouse-and-keyboard desktop session. Town and forest overview images use temporary review cameras; gameplay images use the normal player camera. The forest was loaded directly by the harness to examine it, not reached through a manually activated portal in this run.

The rendering run used review save slot 96. The separate combat run reuses the project's existing combat bot through a tiny subclass that selects slot 98 before combat begins. Neither run calls save; both finish below the autosave interval. No user saves were deliberately read or changed. Only owned test harnesses were added under `game/tests/tools/`.

## Observed results

| Check | Result |
|---|---|
| Town movement | Real `move_right` input for 120 physics frames moved the hero from `(0.0, 0.000069, 14.44986)` to `(7.050719, 0.000717, 14.94015)`, a 7.07 m displacement. |
| Map hotkey | Physical/keycode M opened `WorldMapWindow`; the window's visible property was true. |
| Forest movement | Real `move_up` input for 180 physics frames moved the hero from `(-58.0, 0.075337, 12.4)` to `(-57.99227, -0.730806, -3.269459)`, a 15.69 m displacement. |
| Forest combat | 30-second existing bot run, level 5 knight using the bot's default 4000 XP, 49 starting enemies: 55 player hits, 9 incoming hits, 5 kills, 433 XP gained, 1 item dropped, 1 skill cast, 0 player deaths. |
| Combat movement | Bot recorded 0.8 seconds of stationary time while outside its desired attack reach. This is not a manual movement-quality assessment. |
| Combat outcome | Existing bot's checks passed: it dealt damage, killed enemies and gained XP. This does not establish end-to-end game quality. |

## What the current maps communicate

1. The M map is a five-node zigzag chain. The opening state has Malasugue Town plus four question-mark nodes. It supplies a textual quest objective but no island coastline, town streets, local destination selection, route distance, turn instructions or continuous position within the region. The implementation explicitly draws lines between consecutive entries in a fixed ORDER array and handles mouse motion for tooltips only.
2. Malasugue Town is a compact circular settlement around a fountain and plaza. Its north terrace contains the onward portal. Houses, guild halls, stalls and shrines give it useful social character, but the overview does not communicate an outward road network into a larger inhabited island.
3. Ruined Forest has a west-to-east primary road over a central ravine bridge. The visible camp and tower branches are short spurs. The single crossing is a clear structural bottleneck; the presentation emphasizes traversing toward the far portal more than choosing between different destination routes.
4. The existing art language is worth preserving: isometric dark fantasy, rough cobblestone and timber, small medieval buildings, warm amber pools of light, blue-gray night and mist, muted foliage, luminous cyan portal rings, ornate bronze/gold borders and cyan details. The current UI art reads as an illuminated fantasy chart frame. The proposed island should use that visual vocabulary with readable modern layout and plain labels.
5. The whole-map forest review is very dark at this height. This is a review-camera view, not the ordinary gameplay exposure. Concept art should preserve mood while making roads and landmarks understandable at map scale rather than reproducing the obscurity of this overview.

## Findings to carry into the new design

- Expand Malasugue into an anchor district of a continuous island, with roads visibly reaching several named destinations and portal sites. Do not simply increase empty terrain around the existing town.
- Establish a readable main road loop and meaningful alternate crossings so route choice survives after the first visit. A side activity should preferably rejoin another route or unlock a shortcut.
- Give each teleporter a geographic reason to exist: harbor landing, ridge shrine, forest ruin, mine road or inland sanctuary. Landmarks should be visible from approach roads before the player reads a label.
- Keep local walking directions separate from inter-map portal travel. The M interface should show both parts of a selected journey, including a named portal and its destination, rather than drawing a straight line through terrain.
- Derive routes from traversable data and unlocked transitions; respect locked gates, bridges, interior entrances and discovered destinations. Show a useful failure state when no traversable route exists.
- Preserve existing lore names and town services. Before adding new names, reconcile them with the game's island and faction lore.

## Runtime issues recorded, not fixed

The rendering log contains a startup `!is_inside_tree()` error in `minimap.gd:_draw_markers` at line 142, SubViewport sizing warnings in character preview widgets, repeated unnamed AnimationNodeBlendSpace2D point warnings, and shutdown texture/rendering-server cleanup errors. The combat run also reports six resources still in use at exit. Captures and movement completed, but this was not a warning-free run. These deserve separate triage; the evidence does not establish that they caused the map-design concerns.

## Evidence files

All PNGs are direct native viewport exports at 1920 × 1040.

- `evidence/01-town-gameplay.png`: normal town gameplay camera and current HUD.
- `evidence/02-town-after-walking.png`: after the real movement action.
- `evidence/03-current-M-map.png`: existing map opened by the M key event.
- `evidence/04-town-overview.png`: native geometry from a temporary review camera.
- `evidence/05-forest-gameplay.png`: normal forest gameplay camera.
- `evidence/06-forest-after-walking.png`: after the forest movement action.
- `evidence/07-forest-overview.png`: full forest geometry from its built-in overview viewpoint.
- `evidence/runtime-review.json`: measured movement and M result.
- `evidence/combat_knight.json`: existing combat bot measurements.
- `evidence/runtime-stdout.log`, `runtime-stderr.log`, `combat-stdout.log`, `combat-stderr.log`: retained raw logs.

Harnesses: `game/tests/tools/map_concept_review.gd/.tscn` and `map_concept_combat.gd/.tscn`. The gameplay review is run with `--class=knight --slot=96`; the combat review is run headless with `--class=knight --maps=ruined_forest --seconds=30 --out=<evidence directory>`.
