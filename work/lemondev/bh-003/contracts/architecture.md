# Contract — town buildings and interior kit (builder E)

Read first: `docs/LORE.md` (§5–6, §8), `tools/blender/environment/README.md`, `kit.py`, `masonry.py`,
`assets_town.py` (house_intact is the style reference), `assets_props.py`, `game/src/world/material_library.gd`
(`ENV` table — the only material names the game understands for environment assets; new ones available:
`BH_ClothBlue`, `BH_ClothViolet`, `BH_Silver`, `BH_Plaster`, `BH_Bottle`, `BH_Paper`, `BH_Rope`).

Put new builders in `tools/blender/environment/assets_town2.py` (exteriors) and `assets_interior.py` (interior kit),
register them with `@asset(...)`, and add one import line to `build_assets.py`. Build with
`cd /home/user/beyond-heroes && python3 tools/blender/environment/build_assets.py -- <names>` (bpy module; the
`blender -b` form in the README is the same script). Output: `game/assets/environment/<name>.glb`.

Conventions (from the README): metres, Z-up in Blender (−Y = front = Godot +Z), origin at the bottom centre, `BH_*`
material names from ENV, `<name>-colonly` collision children (use `k.col_box`), sockets as child empties.

## A. New exteriors for Malasugue (match `house_intact`: stone ground floor, timber upper, warm windows)

| name | description | sockets required |
|---|---|---|
| `tavern_exterior` | **The Salted Marlin**: a wide two-storey tavern-inn (~11 × 7 m footprint), stone ground floor with a big double door and wide windows, timber upper floor with a balcony, thatch roof with two chimneys, a hanging **sign board with a carved swordfish** on an iron bracket over the door, barrels by the entrance. | `door` (floor-level point just outside the door centre), `door_light`, `sign_light` |
| `guild_hall_swordfin` | **Swordfin Hall**: stone hall (~10 × 8 m), tall arched door, pillars, a slate/wood roof, two **blue banner poles** with long blue (`BH_ClothBlue`) banners and silver trim hanging either side of the door, a carved swordfish above the arch (silver). | `door`, `door_light`, `banner_l`, `banner_r` |
| `guild_hall_lantern` | **Lantern House**: narrower, taller hall (~8 × 8 m) with a small tower, violet (`BH_ClothViolet`) banners, and a large wrought-iron **lantern** hung above the door (glass `BH_Glass`). | `door`, `door_light`, `lantern_light` |

Also add a `door` socket to a copy of the house: **`house_intact_door`** = identical to `house_intact` plus a `door`
socket (do not modify `house_intact` itself — existing maps depend on it).

## B. Interior kit (the game assembles rooms from these on a 4 m grid)

Walls must line up on the 4 m grid like `wall_straight` (origin at the bottom centre of the segment, length 4 m along X,
thickness ~0.3 m, height 3.6 m; front face −Y). Interiors are viewed from a high camera looking north-down: the
**south** walls use the low `*_low` version so the room stays visible.

| name | description |
|---|---|
| `int_wall_plaster` | Whitewashed plaster wall (`BH_Plaster`) with dark timber posts and a skirting board; 4 m. |
| `int_wall_plaster_window` | Same with a lit window (shutters, sill) — window glass `BH_Glass`. |
| `int_wall_plaster_door` | Same with a door opening (2.2 m) and a wooden door leaf set ajar; socket `door`. |
| `int_wall_plaster_low` | Cutaway: 0.9 m high version (south walls). |
| `int_wall_stone` / `int_wall_stone_low` | Stone-block interior wall for the guild halls (reuse masonry). |
| `int_floor_planks` | 4 × 4 m plank floor tile, 0.1 m thick (`BH_Wood`). |
| `int_ceiling_beams` | Exposed beam set for 4 × 4 m (hang at 3.4 m; may be hidden by the game). |
| `fireplace` | Stone hearth with chimney breast, iron grate, logs; socket `flame` in the firebox, `light`. |
| `bar_counter` | Tavern counter ~4 m with a top, panelling and a foot rail. |
| `bar_back_shelf` | Wall shelf unit with bottles (`BH_Bottle`), mugs, a small keg. |
| `keg_rack` | Rack of 3–4 kegs with taps. |
| `stool`, `bench`, `table_round`, `table_long` | Tavern furniture (chairs and a table already exist as `chair`, `table`). |
| `bed_double`, `wardrobe`, `cabinet`, `crib`, `washstand`, `trunk` | Home furniture (`bed` exists). |
| `cooking_hearth` | Kitchen: iron pot on a tripod over coals (`flame` socket). |
| `desk_writing`, `map_table` | Scholar/cartographer desk with papers (`BH_Paper`), ink, books; a table with a spread map of four islands. |
| `bookshelf_full` | Full bookshelf (`bookshelf` exists — make this richer/taller). |
| `notice_board` | Guild contract board with pinned papers. |
| `weapon_display`, `armor_stand` | Swordfin Hall: wall rack with crossed spears and a stand with plate armour. |
| `lectern`, `lantern_stand` | Lantern House: lectern with an open tome; a tall iron stand with a lit lantern (`light` socket). |
| `guild_banner_swordfin`, `guild_banner_lantern` | Hanging interior banners (~1.2 × 2.4 m) with the emblem modelled in relief (swordfish over crossed blades in silver on blue / golden lantern on violet). |
| `fishing_nets`, `fish_rack` | Net draped on a frame with floats; drying rack with fish. |
| `shrine_small` | Keeper's household shrine: small stone altar with candles and carved creature figures (serpent, giant, beast). |
| `hanging_lantern` | Ceiling lantern on a chain (`light` socket). |
| `rug_round`, `curtain` | Soft furnishing. |

Budgets: furniture 200–2500 tris each, exteriors ≤ 25k tris. Collision boxes for anything you cannot walk through.

## Evidence

Render previews with `tools/blender/environment/render_assets.py` if it works headless, otherwise a Workbench
render (see `tools/blender/characters/preview_enemy.py` for a working headless Workbench setup), into
`work/lemondev/bh-003/evidence/architecture/`, plus `README.md` listing every asset with tris and sockets. Look at
every image and fix problems (floating parts, wrong front, z-fighting, sockets missing).
