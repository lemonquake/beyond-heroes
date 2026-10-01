# bh-029 map builder brief (Builders W1 and W2)

You build map scripts for the Godot 4.7 game Beyond Heroes (`A:\Python\beyond-heroes`) for its new island, **Zarael**.
Read first: `work/lemondev/bh-029/contract.md` (story, theme, house rules), `docs/MAPS.md` (authoring conventions),
`game/src/data/data_zarael.gd` (**the frozen spots every map must honour**), and the Zarael section of
`game/src/data/data_island.gd` (search `bh-029`: places, the road polylines of your maps, and the links). Your map's
road beds, stairs and paths must follow those polylines exactly (the route planner and quest marker walk them).

## Tools and rules
- Godot 4.7.2: `"C:\Users\Lemon PC\Desktop\Godot.exe"`. You MAY run it on `game/` for headless map builds and captures
  of **your own maps** (the Orchestrator has already imported the kit), but never `--import`, never the editor, and never
  kill Godot by image name (only your own PID; prefer `timeout`).
- **Before any headless run, parse-check every script you wrote/edited:**
  `"<godot>" --headless --path game --check-only --script res://src/world/maps/<file>.gd` and grep for `Parse Error`
  (a parse error makes runs hang forever). "Identifier not found" for autoloads (Game, DB, …) is expected noise.
- Probes/captures that boot a hero pass `--slot=96` (W1) / `--slot=97` (W2). Never touch slots 0-2 or `settings.cfg`.
- Write ONLY your map scripts, your capture tool, your evidence dir `work/lemondev/bh-029/evidence/maps_w<n>/`, scratch
  under `work/lemondev/bh-029/scratch/w<n>/`. If you need a change in a shared file (MapBuilder, DataZarael, DataIsland,
  data files, kit), do not edit it: describe it in your final report.
- No Filipino words or real-culture names in anything you write (signposts, comments).

## Read these maps and helpers
- `game/src/world/maps/westreach.gd` (big wild district: terrain, road beds from DataIsland, camps, dressing, exits),
  `game/src/world/maps/settlement_builder.gd` (lattice + `prepare()` that flattens DataIsland roads, `height_at`,
  `keep_clear`, `corridor_rails`), `game/src/world/maps/sundered_reach.gd` and `weeping_causeway.gd` (void/bridge-like maps,
  boss markers), `game/src/world/map_builder.gd` (kit/decor/scatter/terrain/water/mist/light/spawn/exit_zone/enemy_zone/
  wild_camp/dungeon_gate/teleporter/signpost/hide_when/boundary/view/set_bounds).
- Kit: `game/assets/environment/zr_*.glb` — see `work/lemondev/bh-029/evidence/kit_wild/assets.md` (and `kit_town/` if
  present) for sizes, origins, sockets and walkable heights. Existing kit (`rock_*`, `tree_*`, `fern`, `grass_clump`, …)
  may be mixed in sparingly; the island must read as **all-new**: the Zarael pieces lead.
- Textures for `terrain()`: `jungle_floor`, `red_clay`, `blackwire_soil`, `cliff_ochre`, `terrace_paving`, `glyph_stone`
  (look at how westreach passes its texture dict). Materials `BH_*` are applied automatically.
- Gameplay classes you place: `RelayPylon` (`src/world/zarael/relay_pylon.gd`), `WardPylon` (`ward_pylon.gd`),
  `DawnEngine` (`dawn_engine.gd`) — read them; each says what the map must give it.

## Common requirements
- Script `game/src/world/maps/<map id>.gd` (`extends SettlementBuilder` for terrain maps, or `MapBuilder`). Deterministic
  (seeded `rng`). Map defs already exist in `DataMaps.zarael()`; dungeon gates are placed with `dungeon_gate(id, pos, yaw)`
  for every `DataDungeons.gates_on(def.id)` (their spots are in `DataDungeonsZarael.GATES`).
- Spawns (exact ids) and exit zones (exact destinations) from the table below. Every exit zone sits at the map edge
  where its road leaves; `corridor_rails` or boundaries stop the hero walking off the map anywhere else.
- Enemies: `enemy_zone(...)` + `set_meta(&"levels", Vector2i(lo, hi))` for each camp, levels rising with distance from
  the entry, within the map's range. Use ONLY the Zarael monster ids (`DataEnemiesZarael`) listed per map. 8–14 camps per
  wild map, 3–6 monsters each, elite chance 0.1–0.25; keep roads near the entry quieter. Monster GLBs may not exist yet
  (builders are still making them): your map must not instantiate monsters itself (the Spawner does), so it still builds.
- Atmosphere: Zarael is **corrupted**: dusk/night skies with violet-red Blackwire glow on wires and glass, warm torch and
  brazier light, mist in hollows. Lights: keep shadow-casting lights ≤ 2 and total lights reasonable (look at westreach).
  Decoration through `decor()`/`scatter()` (batched), not thousands of `kit()` instances. Keep `scatter` O(n) (no O(n²)).
- Performance: build + navmesh bake under ~15 s on this PC (`tests/tools/time_maps.tscn -- --maps=<id>`), no
  `WARNING:` spam in stderr (each costs ~45 ms in Godot 4.7).
- `view(...)` presets: at least `overview`, `topdown`, and 3–5 close views of the landmarks; `set_bounds(...)`.
- Evidence: a capture tool `game/tests/tools/capture_bh029_w<n>.tscn/.gd` (copy the pattern of
  `tests/tools/capture_maps.gd` / `capture_bh028_special.gd`) that loads your maps and writes PNGs of every view at
  1920x1080 with the real renderer (not headless) to your evidence dir. **Look at every PNG** and revise (up to 3 passes):
  readable from the game camera, nothing floating, no gaps in walkable surfaces, landmarks epic, in theme.
- A walk check: a headless probe that loads the map, bakes the navmesh and asks `NavigationServer3D.map_get_path` from the
  entry spawn to every place of the map (DataIsland places with `map == <id>`) — report any unreachable one.

## W1 — `zr_coilwood` (The Coilwood, 30–36) and `zr_barrens` (The Glasswire Barrens, 36–42)
**Coilwood** (bounds x −140..140, z −100..100): jungle of giant ceiba trees and palms over the Wirewrights' abandoned
step-fields (low terraced earth banks with ruined glyph walls), broken aqueducts, vine curtains on ruin walls, the
Heartwire's relay lines (a few `zr_wire_conduit_4m`/pylons if K1 delivered them, else `zr_relay_pylon`s without chains as
dead relays). Roads: `zc_road*` (paved with terrace stones, overgrown) and the trails. Required:
- spawn `agdao_road` at `DataZarael.CW_WEST` facing east; exit zone at the west edge on the road → `agdao` / `coil_gate`.
- spawn `barrens_road` at `CW_EAST` facing west; exit zone at the east edge → `zr_barrens` / `coil_road`.
- the waypoint `teleporter(&"coil_shrine", ...)` inside a `zr_ruin_shrine` at `CW_SHRINE` (destination: `agdao` /
  `agdao_shrine`, "Agdao"), spawn `coil_shrine` beside it. The shrine area is safe (no camp within 25 m).
- three relay pylons at `CW_RELAYS[i]`: `kit("zr_relay_pylon", …)`, `hide_when(kit("zr_relay_chains", …), DataZarael.RELAY_FLAGS[i])`,
  and `markers.add_child(RelayPylon.new().setup(i + 1))` at the same spot; a Kharvenn guard camp beside each (chain priests
  + others, levels 30–32 / 32–34 / 34–36) with `zr_chain_spike`s round the pylon.
- the Kharvenn camp at `CW_CAMP` (tents, chain racks, spikes, braziers; a strong camp 34–36).
- the Jade Sepulchre gate (`dungeon_gate`) at its `GATES` spot, framed by ruins/ferns.
- monsters: `glyphbound_warrior`, `coil_shaman`, `mossback_idol`, `wireback_stalker`, `relay_mote`, plus `chain_priest`
  and `chain_bearer` at the Kharvenn sites.
**Barrens** (bounds x −130..130, z −100..100): a red cracked plain (`red_clay`, `blackwire_soil` where the Blackwire broke
through) with violet glass growths, ochre rock outcrops and cliffs, the fallen colossus at `GB_COLOSSUS` (landmark, big),
dead pylons. Required:
- spawn `coil_road` at `GB_WEST` facing east; exit west → `zr_coilwood` / `barrens_road`.
- spawn `bridge_road` at `GB_NORTH` facing south; exit north → `bridge_of_death` / `barrens_road`.
- the survivors' camp at `GB_CAMP`: a ring of `zr_ruin_wall`s/palisade and tents, braziers, the waypoint
  `teleporter(&"barrens_shrine", …)` (destination `agdao` / `agdao_shrine`), spawn `barrens_shrine`, and a `bonfire("barrens_camp", …)`
  checkpoint (see `MapBuilder.bonfire`). Safe: no camps within 30 m. (Quillan Ashby the scout stands near
  `GB_CAMP + (3.5, −2)`; keep that spot clear.)
- the Obsidian Engine and Veinworks gates (`dungeon_gate`) at their `GATES` spots.
- monsters: `wiresick_husk`, `arc_sentinel`, `chain_priest`, `chain_bearer`, `glasswire_scorpion`, `relay_mote`.

## W2 — `bridge_of_death` (42–46) and `zr_citadel` (The Heart Citadel, 46–52)
**Bridge of Death** (bounds x −40..40, z −170..160): a south approach on a cliff ledge (z 136..160) with the south
`zr_bridge_gatehouse` at z ≈ 136, then **the span**: `zr_bridge_span_8m` segments end to end from z 132 to z −110 over a
bottomless gorge (no terrain under it: gorge walls `zr_cliff_ochre`/rocks far to the sides and deep below, mist and dark
far down, `zr_bridge_pier`s hanging under every ~5th segment), the **far platform** (a wide 28 x 28 m deck at z −104..−132
built from span pieces side by side or a `floor_tiles`/`walk_slab` surface dressed with the kit), then the north gatehouse
at z ≈ −146 and a short landing to the north edge. The deck must be one continuous walkable surface (check the navmesh).
Boundaries along both rails. Required:
- spawn `barrens_road` at `DataZarael.BR_SOUTH` facing north; exit south edge → `zr_barrens` / `bridge_road`.
- spawn `citadel_road` at `BR_NORTH` facing south; exit north edge → `zr_citadel` / `bridge_road`.
- the **north gate seal**: a blocking `StaticBody3D` across the north gatehouse passage with a violet-red ward glow,
  `hide_when(seal, DataZarael.F_BRIDGE)` (it disappears once Varrogh falls). The exit zone beyond it is gated with
  `exit_zone(..., flag = DataZarael.F_BRIDGE, hint = "The north gatehouse stays sealed while Varrogh holds the span.")`.
- three ward pylon **pairs** at z = `BR_PYLONS[vault]` (one `zr_bridge_pylon` each side, outside the rails), each pair
  handed to one `WardPylon.new().setup(vault, [left, right], [left arc socket, right arc socket])` added to `markers` at
  the pair's centre (it recolours them and throws the lightning). Read `ward_pylon.gd`.
- **Varrogh**: a `boss_spawn` marker at `BR_BOSS` (see `weeping_causeway.gd`: group `boss_spawn`, meta `boss` =
  `&"deathspan_colossus"`, meta `flag` = `DataZarael.F_BRIDGE`), plus a `summons_` zone for its adds (`span_warden`).
- monsters on the span: `span_warden`, `wire_leaper`, `ward_eye` (4–6 camps spread along the span, levels 42–46).
- epic: the span must look monumental from the game camera; wire channels glow; pylon arcs; wind/mist; distant cliffs.
**Heart Citadel** (bounds x −100..100, z −85..85): a temple-fortress on a stepped rise: `zr_citadel_wall`s and towers
round it, a gate on the south road, a ceremonial avenue (glyph steles, serpent statues if available) up stepped plazas to
the **Dawn Engine** at `HC_ENGINE`, Kharvenn siege works (tents, chain racks, chains clamped to the Engine's base) and
dead Agdao lamps. Required:
- spawn `bridge_road` at `HC_SOUTH` facing north; exit south edge → `bridge_of_death` / `citadel_road`.
- the Dawn Engine: `var m := kit("zr_dawn_engine", …)`; `markers.add_child(DawnEngine.new().setup(m))` at the same spot.
- the arena: clear ground of radius `HC_ARENA_R` round the Engine (a little south of it), a `boss_spawn` marker at
  `HC_ABBOT` (meta `boss` = `&"leash_abbot"`, meta `flag` = `DataZarael.F_ABBOT`), a `summons_` zone.
- monsters: `leash_knight`, `chain_priest`, `chain_bearer`, `gigas_spawn`, `heartwire_wraith` (levels 46–52).
- a few `MapBuilder.hide_when` touches are welcome (e.g. Kharvenn chain props round the Engine vanish on
  `DataZarael.F_RESTORED`).

## Final message
A concise report: files written, per map the spawn/exit/marker positions you actually used, build+bake time, the walk
check result, triangle/light counts if measured, evidence PNG list, known limitations, and any change you need in a
shared file.
