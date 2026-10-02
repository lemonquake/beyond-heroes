# Map design: authored groups, dungeon room roles and the prepared Kenney pieces

Map-design pass of 3 October 2026 (brief: `docs/CLAUDE_MAP_DESIGN_AND_DUNGEON_ASSETS.txt`). This page explains how the
dressing works so it can be extended without breaking routes, quality levels or frame time.

## Prepared pieces (`game/assets/environment/kd_*.glb`)

`tools/blender/environment/prepare_kenney.py` (Blender 5.2, headless) turns each accepted Kenney package from
`assets_src/map_design_20261003/canonical/` into one runtime GLB:

- every part joined into **one mesh with an identity transform** (multi-part sources keep all their parts);
- scaled to game metres (a rule per model: target height or uniform scale), seated on its origin, front +Z;
- part materials renamed to the shared `BH_*` contract, so `MaterialLibrary` gives them the game's lit, textured,
  theme-aware materials. Flat-colour parts map by source material name; palette-textured parts (pirate, graveyard,
  dungeon kits) map per face by the palette colour under the face's UV centre, so a barrel keeps staves and hoops apart;
- animations, armatures and skins dropped (a decorative chest is not a loot chest);
- box collision (`<name>-colonly`) for furniture, large rocks and tree trunks; none for small details.

Receipts per model (source and derived SHA-256, scale, part-to-material table, triangles, surfaces, bounds) are written
to `work/map-design/prepared/`. Re-run: `blender -b --factory-startup -P tools/blender/environment/prepare_kenney.py -- [names]`.
New `BH_*` materials added for them: `BH_Foliage`, `BH_FoliageDark`, `BH_Rock`, `BH_Terracotta`, `BH_Produce`,
`BH_MushroomPale` and three muted flower accents.

`python tools/map_design_inventory.py` rebuilds `output/map-design-20261003/assets/accepted_assets.md` (where every
piece is used, from real map builds) and `ASSET_CREDITS_MAP_DESIGN.md`.

## Authored groups (`DataVignettes`, `MapBuilder.vignette` / `place_near`)

A vignette is a small arrangement with a purpose — a woodpile, a supply corner, a bench with a view, a cargo stack, a
burial bay — defined once in `src/data/data_vignettes.gd` and placed with one call:

```gdscript
clear_fn = _clear_here                     # the map's walking lines: (x, z, r) -> bool
place_near("timber_store", prefer, around, 6.0, 12.0, yaw)   # nearest clear spot to `prefer` in a ring round `around`
vignette("wreck", Vector3(x, SEA_Y - 1.6, z), 35.0, {"on_ground": false, "check": false})
```

- Each piece is grounded on its own spot (or, with `on_ground: false`, stands at the origin's height: quays, roofs and
  Agdao's terraces — never the terrain under a raised surface).
- A group is skipped, never forced, when its footprint touches a walking line (`clear_fn`), another group or a solid
  piece already placed (`touches_solid`: every colliding kit piece is remembered as an oriented footprint). Skips are
  listed on the map (`vignettes_skipped`), placements on `vignettes`.
- Piece kinds: `k` collides, `d` decoration, `b` batched small decoration (thinned on Low by `LITE_KEEP`), `o` optional
  detail (left out on Low). Landmarks and colliders never change with quality.
- Colliding pieces are **batched solids** (`MapBuilder.solid`): their visuals join the per-24 m-cell MultiMesh batches
  and their own collision shapes stand on a StaticBody3D under Props (so the navmesh carves round them). Decoration is
  batched too. A new group therefore adds batches, not a node and draw calls per piece.

## Dungeon room roles (`DataDungeonRoles`, `dungeon.gd` `_dress_rooms`)

Every floor is split into rooms: each storey's connected cells, partitioned into zones grown from the floor's markers
(arrival, seal, goal, boss) plus evenly spread seeds (about one zone per eight cells). Roles:

| Role | Where | What it gets |
| --- | --- | --- |
| arrival | the zone with the arrival portal | a theme landmark motif and a threshold inlay under the spawn |
| seal | the seal / goal zones | one or two peripheral motifs; the fight's ground stays clear |
| boss | the arena | the theme's one silhouette in the two dressable cells farthest from the boss, nothing else |
| traversal | small zones on a basin or bridge edge | edge motifs; parapet details along the water |
| work / function | the rest, alternating by size | storage and support, or the theme's own function (burial, study, forge, organic...) |

Motifs (`DataDungeonRoles.M`) stand in a 1.6 m band against a wall (or in a corner for the big bespoke pieces), so a
4 m cell keeps 2.4 m of floor. Never dressed: marker cells (portals, seal, boss, camps, chests), the spawn cells beside
portals, cells next to stairs or bridges, one-cell corridors and the south (camera) side. Each room uses different
motifs; deep and growth floors swap a work motif for the theme's decay motif. `BY_DUNGEON` keeps dungeons that share a
theme apart (the three hideouts, the two crypts). Motif fire (`@fire`) and warm pools (`@glow`) are capped at five per
floor and off on Low. Rooms, motifs and the seed are recorded on the map (`rooms`, `room_seed`, `room_keep`).

## Ambient accents (`AmbientAccents`, `MapBuilder.accent`)

One node per map plays an existing sound now and then at an authored spot near the hero (forge fire, quay water, wind
on the bridge, basin water), through `Audio.play_at_if_free`, which never takes a voice from combat. Low plays them half
as often. Ambience beds and reverb per map are unchanged.

## Tools

| Tool | Use |
| --- | --- |
| `tests/tools/map_design_probe.tscn -- --cmd=build --maps=a,b` | build maps headless; report groups, skips and a census |
| `... --cmd=rooms [--floors=all]` | every dungeon floor's rooms, roles and motifs |
| `tools/gdcheck.sh <files>` | compile scripts with the autoloads loaded (catches errors `--check-only` misses) |
| `tests/tools/capture_map_design.tscn -- --set=all --tag=after --lite=0` | matched gameplay and clean captures |
| `python tools/map_design_compare.py` | side-by-side before/after JPGs |
| `python tools/perf_matrix.py run --set map-design --root output/map-design-20261003/perf ...` | matched frame-time runs (`--game` for a frozen copy) |
| `tests/unit/test_map_design.gd` | contract, batching, determinism, quality invariants, theme isolation, room reachability |
