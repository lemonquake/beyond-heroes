# bh-003 architecture evidence (Builder E)

Town buildings for Malasugue and the interior kit, built procedurally with `bpy` (4.4 pip module):

- Builders: `tools/blender/environment/assets_town2.py` (category `town2`) and `assets_interior.py` (category
  `interior`), registered via one import line in `build_assets.py`.
- Output: `game/assets/environment/<name>.glb` (43 new GLBs).
- Build: `python3 tools/blender/environment/build_assets.py -- town2 interior` (or asset names).
- Preview: `tools/blender/environment/preview_town2.py` (headless Workbench). It re-imports each GLB and renders
  front, front 3/4, back 3/4 and the high game camera. It can also render close-up detail tiles (`--detail`) and a
  collision x-ray tile (`--col`).
- Room test: `preview_town2.py -- --room` assembles an 8 × 8 m tavern room on the 4 m grid → `room_assembly.png`.

**What the previews show.** Workbench shows material colours from the kit table, cavity and shadow. It checks
shape, grounding, facing and sockets, not the final look. In the previews:

- The ground has dark lines on the 4 m grid. The red cross marks the origin, and the red stub points to the front (−Y).
- Magenta balls are sockets, labelled with their names. Labels are drawn even when a socket is hidden behind geometry.
- Hanging banners are lifted for display only, and the sheet notes the lift.

**Coordinates.** All numbers are asset-local Blender coordinates in metres: Z up, −Y = front = Godot +Z. Godot
coordinates are (x, z, −y).

**Materials.** Every material name is in the ENV table of `game/src/world/material_library.gd`. This was checked on
the exported GLBs. The new names used are BH_ClothBlue, BH_ClothViolet, BH_Silver, BH_Plaster, BH_Bottle, BH_Paper
and BH_Rope. `kit.get_mat` only knows the old names, so `assets_town2.py` registers export colours for the new ones
in `kit.MATERIALS` at import time. kit.py itself is not modified.

## A. Exteriors (budget ≤ 25k tris)

Origin is at the bottom centre of the footprint (`recenter=False`), and the door faces −Y. The door socket sits on the
ground (z = 0), outside the collision box and in front of any step.

| asset | tris | footprint (bbox x × y × h) | collision | sockets |
|---|---|---|---|---|
| `house_intact_door` | 23,778 | 8.48 × 7.37 × 9.60 | 1 box (walls) | **door (0, −4.00, 0)**, door_light (0, −3.40, 2.20) |
| `tavern_exterior` | 24,668 | 12.49 × 9.54 × 10.53 | building box + barrels/crate | **door (0, −4.80, 0)**, door_light (0, −4.35, 2.60), sign_light (0, −5.70, 3.39) |
| `guild_hall_swordfin` | 22,882 | 11.28 × 10.19 × 9.20 | hall box + 2 pillars + 2 banner poles | **door (0, −5.35, 0)**, door_light (0, −4.80, 4.00), banner_l (−3.30, −5.25, 6.25), banner_r (3.30, −5.25, 6.25) |
| `guild_hall_lantern` | 22,662 | 9.58 × 10.56 × 16.85 | hall box + tower box | **door (0, −4.85, 0)**, door_light (0, −4.45, 2.20), lantern_light (0, −5.00, 3.11) |

- **house_intact_door** calls the unmodified `house_intact` builder with house_intact's own RNG and noise seeds, then
  adds the `door` socket. Built side by side in this environment, both have identical geometry (12,945 verts, same
  vertex checksum). The shipped `house_intact.glb` was built with Blender 5.2 and differs by 13 exported vertices from
  a bpy 4.4 build. Tri counts are equal. `house_intact.glb` itself was not rebuilt or touched.
- **tavern_exterior** (The Salted Marlin, walls 11 × 7 m):
  - Ground floor: stone, with a 2 m double door, two 1.6 m windows and a stone lintel with keystone.
  - Upper floor: timber-framed, with a balcony on the right half and a balcony door.
  - Roof: thatch, with a stone chimney and a brick chimney.
  - Sign: an iron bracket from the floor band holds a board parallel to the façade, 1.2 m out from the wall, with a
    silver swordfish in relief on both faces.
  - Wall lanterns flank the door, and barrels and a crate stand by the entrance.
  - The first build was 32.8k tris, over budget. Blocks were made larger and chimneys now start at the eaves (the part
    inside the roof was hidden anyway).
- **guild_hall_swordfin** (walls 10 × 8 m):
  - Stone hall with a tall round-arched door (2.2 m wide, arch top at 4.45 m), two round pillars, arched side windows,
    a cornice and a slate roof.
  - Two free-standing banner poles carry long BH_ClothBlue swallow-tail banners with silver trim and a silver
    swordfish.
  - A large silver swordfish over two crossed silver blades sits above the arch.
  - `banner_l` / `banner_r` mark each banner's hang point (the crossbar centre). Left = −X, as seen from the front.
- **guild_hall_lantern** (walls 7 × 7 m, taller):
  - Stone ground floor with an arched door, timber upper floor, and a steep wooden-shingle roof with the gable facing
    the street.
  - A 2.6 m square stone tower at the back-left rises to about 16.9 m, with lit slit windows.
  - Two wall-hung BH_ClothViolet banners carry the gold lantern emblem.
  - A big wrought-iron lantern with BH_Glass panes hangs on a scrolled bracket over the door. `lantern_light` is inside
    the lantern.

## B. Interior kit (furniture budget 200–2500 tris)

- **Walls** are 4.0 m along X and 0.30 m thick, centred on y = 0, and 3.6 m tall (0.9 m for the `_low` versions).
  Origin is at the bottom centre. The room side is −Y, and timber is on both faces.
- **Neighbouring walls** share a single 0.14 m corner post, because each segment carries a 0.07 m half post at each
  end.
- **Floor tiles** are 4 × 4 m and 0.1 m thick, so the top is at z = 0.1.
- **Wall-standing furniture** (`recenter=False`) has its back on +Y, so it can be pushed against a wall.
- **Free-standing furniture** is re-centred like `assets_props`.
- **Ceiling pieces** keep the origin on the floor.
- **Hanging banners** follow `banner_torn`: the origin is at the rod.

| asset | tris | bbox min → max (x, y, z) | col | sockets / notes |
|---|---|---|---|---|
| `int_wall_plaster` | 240 | (−2, −0.21, 0) → (2, 0.21, 3.6) | box | braces, mid post, rail |
| `int_wall_plaster_window` | 726 | (−2, −0.25, 0) → (2, 0.25, 3.6) | box | light (0, −0.40, 1.70); BH_Glass 1.3 × 1.3 m, shutters, sill candle |
| `int_wall_plaster_door` | 728 | (−2, −1.24, 0) → (2, 0.21, 3.6) | 3 boxes (opening free) | **door (0, −0.90, 0)**; opening 1.3 × 2.2 m; leaf hinged at x = −0.65, 60° ajar into the room (−Y), no collision on the leaf |
| `int_wall_plaster_low` | 188 | (−2, −0.21, 0) → (2, 0.21, 0.9) | box | south cutaway |
| `int_wall_stone` | 1,692 | (−2.01, −0.19, 0) → (2.01, 0.19, 3.61) | box | masonry + capstones |
| `int_wall_stone_low` | 644 | (−2, −0.2, 0) → (2, 0.2, 0.91) | box | |
| `int_floor_planks` | 1,420 | (−2, −2, 0) → (2, 2, 0.1) | box | boards along X, staggered joints |
| `int_ceiling_beams` | 488 | (−2, −2, 3.39) → (2, 2, 3.82) | none | beams x = ±1 along Y (bottom 3.4 m), joists every 0.5 m |
| `fireplace` | 1,944 | (−1.3, −0.92, 0) → (1.3, 0.45, 3.59) | 2 boxes | flame (0, −0.05, 0.45), light (0, −1.05, 0.90); back at y = +0.45 |
| `bar_counter` | 914 | (−2.02, −0.54, 0) → (2.02, 0.41, 1.38) | box | customer side −Y, foot rail |
| `bar_back_shelf` | 2,400 | (−1.55, −0.29, 0) → (1.55, 0.25, 2.4) | box | bottles, mugs, small keg; back at y = +0.25 |
| `keg_rack` | 1,974 | (−1.05, −0.71, 0) → (1.05, 0.35, 1.05) | box | 3 kegs, brass taps toward −Y, drip bucket |
| `stool` | 236 | 0.42 × 0.39 × 0.70 | box | |
| `bench` | 276 | 1.81 × 0.40 × 0.47 | box | |
| `table_round` | 578 | 1.25 × 1.25 × 0.95 | cylinder | Ø 1.24 top at 0.78 m |
| `table_long` | 1,000 | 3.01 × 0.90 × 1.08 | box | |
| `bed_double` | 1,444 | 2.13 × 1.62 × 1.36 | box | headboard at +X |
| `wardrobe` | 524 | (−0.73, −0.36, 0) → (0.73, 0.34, 2.32) | box | |
| `cabinet` | 438 | (−0.53, −0.29, 0) → (0.53, 0.27, 1.21) | box | |
| `crib` | 1,280 | 1.00 × 0.73 × 0.92 | box | |
| `washstand` | 572 | (−0.35, −0.23, 0) → (0.40, 0.23, 1.0) | box | |
| `trunk` | 696 | 0.93 × 0.54 × 0.57 | box | |
| `cooking_hearth` | 1,482 | (−0.6, −0.73, 0) → (0.68, 0.61, 1.36) | cylinder | flame (0, 0, 0.25), light (0, 0, 0.70) |
| `desk_writing` | 812 | (−0.7, −0.37, 0) → (0.7, 0.35, 1.26) | box | papers, ink + quill, books, candle |
| `map_table` | 1,744 | 1.80 × 1.20 × 1.13 | box | map of four islands (BH_Moss on BH_Paper), compass rose |
| `bookshelf_full` | 2,352 | (−0.96, −0.25, 0) → (0.99, 0.25, 3.06) | box | 2.8 m, 6 shelves, scroll cubby |
| `notice_board` | 1,264 | (−1.15, −0.32, 0) → (1.15, 0.32, 2.63) | box | pinned contracts, wax seals |
| `weapon_display` | 1,420 | (−1.04, −0.17, 0.5) → (1.04, 0.08, 2.75) | box | wall-hung (back at y ≈ +0.08); crossed spears, swordfish shield, 2 swords |
| `armor_stand` | 1,894 | 0.80 × 0.70 × 2.01 | box | plate harness, blue tabard |
| `lectern` | 660 | 0.60 × 0.48 × 1.26 | box | open tome, violet ribbon |
| `lantern_stand` | 604 | (−0.19, −0.3, 0) → (0.6, 0.3, 2.6) | box | light (0.45, 0, 1.71) |
| `guild_banner_swordfin` | 940 | (−0.8, −0.09, −2.46) → (0.8, 0.04, 0.36) | none | 1.2 × 2.4 m; silver swordfish over crossed blades on blue |
| `guild_banner_lantern` | 816 | (−0.8, −0.08, −2.46) → (0.8, 0.04, 0.36) | none | golden eye-flame lantern on violet |
| `fishing_nets` | 2,140 | (−1.36, −0.58, 0) → (1.36, 0.05, 2.1) | box | cork + glass floats, rope coil, basket |
| `fish_rack` | 1,084 | 2.40 × 1.17 × 1.83 | box | 18 fish |
| `shrine_small` | 1,246 | (−0.6, −0.3, 0) → (0.6, 0.3, 1.46) | box | light (0, −0.30, 1.20); serpent / giant / beast figures |
| `hanging_lantern` | 668 | (−0.18, −0.21, 1.92) → (0.18, 0.21, 3.4) | none | light (0, 0, 2.28); ceiling plate at 3.4 m |
| `rug_round` | 1,724 | Ø 2.2 × 0.02 | none | |
| `curtain` | 1,140 | (−1.05, −0.2, 0.02) → (1.05, 0, 2.53) | none | rod at 2.5 m, panels tied back |

## Images

| file | what |
|---|---|
| `<asset>.png` | per-asset sheet (front, front 3/4, back 3/4, game camera; exteriors + some pieces also detail and collision tiles) |
| `overview_exteriors.png`, `overview_kit.png`, `overview_misc.png` | front 3/4 grids |
| `room_assembly.png` | 8 × 8 m tavern room from the kit on the 4 m grid: game camera + 3/4 |

## Known issues / notes for integration

- **Floor thickness.** `int_floor_planks` is 0.1 m thick. Furniture origins are at z = 0, so furniture must be placed at
  +0.1 m on top of plank tiles, or the tile lowered by 0.1 m. In `room_assembly.png` furniture is at z = 0 and sinks
  10 cm, and `rug_round` is hidden under the floor.
- **Wall-hung and ceiling pieces need matching heights.** `weapon_display` starts at z = 0.5 with its back plate at
  y ≈ +0.08, so place it flush against the wall face. `hanging_lantern` and `int_ceiling_beams` assume a 3.4 m
  ceiling.
- **Budget.** Exteriors come in close to the 25k budget: 22.7k–24.7k tris.
- **Guild hall doors are closed.** The door leaves are modelled closed and the door opening has collision. The
  `door` socket is the interaction point.
- **Unused socket position.** `int_wall_plaster_door`'s socket is on the room (−Y) side. For a door on a wall rotated
  180° the game must use the rotated socket position.
- **Previews are Workbench only.** EEVEE `render_assets.py` was not used or tested.
- **Nothing was checked in Godot.** No Godot import or in-game view (not allowed for builders).
- **Build log.** `build_assets.py` appends to `tools/blender/environment/build_log.txt` on every run (existing tool
  behaviour), so that file has new lines.
