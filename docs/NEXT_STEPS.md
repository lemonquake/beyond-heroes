# Beyond Heroes — Next Steps (handoff from run bh-003)

This file is the plan for the next working session. Read it together with `docs/LORE.md` (the lore bible every
agent must follow) and `work/lemondev/bh-003/contract.md` (the run contract and invariants).

Branch: `update-0.01-q1u5d0` (pushed). Last commit before this file: `7af4e2b`.
Engine: Godot 4.4.1. Tests: `GODOT=<path to godot> bash tools/run_tests.sh` → 3578 checks, 0 failures at handoff.

---

## 1. What is DONE (committed and pushed)

| Area | State | Where |
|---|---|---|
| Lore bible | Done. World of Jre, 4 islands, Malasugue, Gigas/Tyrants/Oros, Holy War, tiers E–SSS, 2 guilds, town roster. Invented names are marked *provisional*. | `docs/LORE.md` |
| Tiers & guilds | Done: join/transfer/promotion (level + deed + fee), perks, Accord bonus, equip gating by rarity, shop/inn discounts, bounty gold, potion bonus, save round-trip, HUD emblem + guild crest + "Well Rested" tag, character-sheet section, tier award popup. | `src/data/data_guilds.gd`, `src/core/guilds/guild_rules.gd`, `hero_data.gd`, `hud.gd`, `character_window.gd`, `ui_root.gd` |
| Inn & services (logic) | Done: `NpcServices.rest` (exact fee, full restore, cleanse, Well Rested 15 min), `mystic_heal` (Seris, paid). Dialogue services `rest`, `mystic_heal`, `promote`, `join_swordfin`, `join_lantern` with confirm dialogs. Dialogue placeholders `{rest_fee}`, `{next_tier}`, `{promo_fee}` … and conditions `guild`, `no_guild`, `tier_min`, `can_promote`, `rested` … | `npc_services.gd`, `dialogue.gd`, `dialogue_box.gd` |
| Enemy models | Done: 16 enemies incl. new Goblin Skulker, Orc Reaver, Ogre Crusher, quadruped Dire Wolf (own rig, `creature_meta.json`), floating Aether Wisp (procedural animator in `CharacterVisual`). All clip lengths verified at export. | `game/assets/characters/*.glb`, `tools/blender/characters/enemy_*.py`, `tools/blender/creatures/` |
| Enemy runtime | Done: hit materials (flesh/ichor/bone/stone/aether/shadow), blood sprays, ground stains + blood pools (bounded, `FX.MAX_STAINS`), Blood Effects setting, death clip from the killing blow (`death_back/_fwd/_crumple`), corpse decay (fresh → darken → dissolve, `Enemy.MAX_CORPSES`), death styles (crumple/ash/collapse/implode/smoke), traits (reassemble, devour, stealth, pickpocket, aim_line, cowardly, enrage, lob fire-pot/boulder, core_overload, coffin_shield, howl/warcry). | `src/actors/enemy/enemy.gd`, `src/vfx/gore.gd`, `src/vfx/lob.gd`, `src/autoload/fx.gd`, `data_enemies.gd` (`LOOK` table) |
| Townsfolk models | Done (not yet used in game): `elder, scholar, smith, matron, fisher, merchant, officer, bard, traveler` (.glb). Main garment is tintable (`BH_Cloth_Primary`). | `game/assets/characters/` |
| Buildings & interior kit | Done (not yet placed): `tavern_exterior`, `guild_hall_swordfin`, `guild_hall_lantern`, `house_intact_door` + 39 interior pieces. Dimensions/sockets: `work/lemondev/bh-003/evidence/architecture/README.md`. | `game/assets/environment/` |
| UI art | Done: tier emblems (`assets/ui/tiers/tier_*.svg`), guild banners/crests (`assets/ui/guilds/`), 13 new NPC portraits (`assets/ui/portraits/`). | |
| Door system | Code done, not yet used: `DoorPortal` (interactable) and `Game.door_travel(map, spawn)` (fade, no loading screen). `MapDef.interior` / `parent_map` fields added. | `src/world/door_portal.gd`, `game.gd` |

---

## 2. BUG to fix first: floating NPCs in town (reported by the user)

**Symptom:** townspeople in Malasugue float above the ground.

**Most likely cause (not yet verified — confirm before fixing):** `Game.load_map()` adds the map and calls
`NpcDirectory.populate(map)` in the same frame. `NpcDirectory.ground_height()` raycasts down against the physics
space, but freshly added terrain/floor colliders are usually not in the physics space until the next physics step,
so the ray misses and the NPC keeps `p.y = 0`. The town terrain is not flat (`sanctuary.gd::_height`, and the
terrace is at y = 2), so NPCs end up floating (or sunk) wherever the ground is not exactly 0.

**Fix options (pick one, then verify with a render):**
1. In `NpcDirectory.populate`, compute the height from the map builder's height function instead of a ray (the map
   knows its terrain `height_fn`; expose it on `MapRoot`, e.g. `MapRoot.ground_at(x, z)`), with the ray only as a
   fallback for floors/stairs.
2. Or defer placement: spawn NPCs, then `await get_tree().physics_frame` once and snap each NPC down with the ray.
3. Also add a simple safety: NPCs (StaticBody3D) re-snap once in `_ready()` after the first physics frame.

**Test to add:** `test_maps.gd` (or a new `test_npcs.gd`): load `sanctuary`, populate, wait 2 physics frames, and for
every NPC assert `abs(npc.y - ground_ray_y) < 0.1`. Do the same for every interior map once they exist.

Also check the Hooded Stranger (appears later via `presence`) and any NPC placed on the terrace.

---

## 3. Remaining work (in order)

### 3.1 Place the new buildings in Malasugue (`src/world/maps/sanctuary.gd`)
- Swap the 5 `house_intact` lots to `house_intact_door` and give each a `DoorPortal` + an outside spawn
  (`door_<interior_id>`, 1.6 m in front of the door socket, facing out). Door socket (Godot, local) = `(0, 0, 3.4)`.
- Add the three new buildings. Proposed lots (check with a top-down render; fence radius is 40 m, keep ≥ 1 m clear):
  - **The Salted Marlin** `tavern_exterior` at `(-29.5, 0, 13.5)`, yaw 90 (door faces +X toward the plaza).
    Remove the tree at `(-30, 0, 18)`. Door socket local `(0, 0, 4.8)`, `sign_light (0, 3.4, 5.7)`.
  - **Swordfin Hall** `guild_hall_swordfin` at `(33, 0, -5)`, yaw -90. Remove the tree at `(31, 0, -6)`.
    Door `(0, 0, 5.35)`; banner sockets `banner_l/r`.
  - **Lantern House** `guild_hall_lantern` near `(-31, 0, -9)`, yaw ~90. **Tight fit** against the house lots at
    `(-25, 2)` and `(-22, -16)` — verify, rotate or move. Remove the tree at `(-31, 0, -4)`. Door `(0, 0, 4.85)`.
- Update `_greenery()` avoid list and `_splat()` path targets so grass/trees don't grow through the new buildings
  and a path leads to each door. Add lights at `door_light` / `sign_light` / `lantern_light` sockets.
- Rename the town's display name to **"Malasugue Town"** in `data_maps.gd` (keep the id `sanctuary` for saves).

### 3.2 Interior maps (8)
Add to `data_maps.gd` with `interior = true`, `is_town = true`, `waypoint = false`, `parent_map = &"sanctuary"`,
`builder = "res://src/world/maps/interior.gd"`. Write one builder `interior.gd` whose `compose()` switches on `def.id`.

| id | building | size | key props | people |
|---|---|---|---|---|
| `int_tavern` | The Salted Marlin | 16 × 12 | bar_counter, bar_back_shelf, keg_rack, fireplace, table_round + stool, table_long + bench, hanging_lantern, curtain ("Rooms") | Pilar (innkeeper, behind the bar), Ciro (bard, on a rug by the fire), Old Tasyo (table), Venna Kail (by the fire) |
| `int_swordfin` | Swordfin Hall | 16 × 12 stone | guild_banner_swordfin ×2, weapon_display, armor_stand ×2, notice_board, map_table, desk_writing | Commander Rhea Talvanne, Dax Mercado (registrar) |
| `int_lantern` | Lantern House | 12 × 12 stone | guild_banner_lantern ×2, bookshelf_full ×3, lectern, lantern_stand ×2, desk_writing | Archivist Oren Vale, Lio Sanvar (registrar) |
| `int_netmender` | house lot (-25, 2) | 8 × 8 | fishing_nets, fish_rack, cooking_hearth, bed, table, trunk | Nena Lagdameo |
| `int_cartographer` | house lot (25, 6) | 8 × 8 | map_table, desk_writing, bookshelf_full, rug_round | Ibarra Quell |
| `int_widow` | house lot (-17, 23) | 8 × 8 | bed_double, crib, washstand, cabinet, candles, shrine_small | Mirasol Hald |
| `int_keeper` | house lot (23, -14) | 8 × 8 | shrine_small, bookshelf_full, lectern, candles | Keeper Tomas Dalisay |
| `int_refugee` | house lot (-22, -16) | 8 × 8 | bedroll, trunk, table, chair, cooking_hearth | Yusra Ven |

Layout rules (from the kit measurements):
- Walls: `int_wall_plaster` / `_window` / `_door` / `_low`, `int_wall_stone` / `_low` — 4 m long along X, origin at
  the bottom centre, front (+Z) = room side. Use `MapBuilder.room(rect, {north/east/west: piece, south: *_low,
  floor: false, pillars: false, swap: {...}})`.
- Floors: `int_floor_planks` is 4 × 4 × **0.1 m** with the origin at the bottom → place tiles at `y = -0.1` so the top
  is at 0 (otherwise furniture sinks 10 cm and `rug_round` disappears). Add `walk_slab()` colliders under the floor.
- The exit is a gap in the **south** low wall with a `DoorPortal` back to `sanctuary` / `door_<id>`, and a `start`
  spawn just inside (yaw 180). Interiors need a `start` spawn (death respawn in towns uses it).
- Ceiling pieces assume 3.4 m; `weapon_display` hangs from y = 0.5; banners hang downward from their origin
  (≈ 2.46 m long) — place their origin at ~3.2 m on a wall.
- Environment: no sky, warm low ambient, 2–4 flickering lights (fireplace socket `light`, hanging lanterns).
- `set_bounds()` and a `view("room", ...)` for captures.

### 3.3 NPC roster and dialogue
- Create `src/data/data_npcs_town.gd` with the 13 new NPCs (see `docs/LORE.md` §6 table) and register them in
  `DB` next to `DataNpcs.build()`. Each has `map` = its interior id, a model from the townsfolk set, a tint, a
  portrait (`assets/ui/portraits/<file>.svg`, list in `contracts/ui_art.md`), `idle_anims` limited to the clips
  townsfolk have (`idle, idle_look, idle_adjust, interact_talk`), and a dialogue graph of 6–12 nodes that is rooted
  in the lore (each person knows only their corner of the world; tone rules in LORE §8).
- Registrars: **Dax** (Swordfin) and **Lio** (Lantern) offer `join_*`, `promote` (use `{next_tier}`,
  `{promo_fee}`, `{promo_level}`, `{promo_deed}` and the `can_promote` / `guild` / `tier_min` conditions), and explain
  tiers/perks. Guildmasters give lore (Kharvenn Gigas / the Binding, the Oros, the Rekindling doctrine).
- **Pilar** (innkeeper): `{"service": "rest"}` choice "Take a room ({rest_fee} gold)" + rumors that change with world
  flags. Update **Seris**: her "Heal my wounds" becomes the paid `mystic_heal` ("{mystic_fee} gold") and she points
  people to the Salted Marlin.
- Move existing NPCs onto the townsfolk models: Maelis → `elder.glb`, Tovin → `merchant.glb`, Brannoc →
  `smith.glb` (keep Seris/Stranger on `mage.glb`, Hald on `knight.glb`). `Npc._ready` picks the fidget set from the
  model path — make it fall back to `idle_look/idle_adjust` for townsfolk.
- Replace "Hero Sanctuary" wording in `data_npcs.gd` / `data_maps.gd` loading hints with Malasugue
  (the terrace keeps the name "Sanctuary Terrace").
- Tests: extend `test_shops_dialogue.gd::test_data_is_consistent` (already checks every node/choice target and
  portrait) — it will cover the new NPCs automatically once they are in `DB.npcs`; add checks that every new NPC's
  map exists and every `service` value is one the dialogue box handles.

### 3.4 Put the new enemies into the world
- Add `goblin_skulker`, `orc_reaver`, `ogre_crusher` (and more `dire_wolf` packs) to `enemy_zone` lists in
  `ruined_forest.gd` (e.g. a goblin camp near the burnt village, an orc scout band + one ogre near the collapsed
  watchtower). Check `Spawner` level ranges.
- `model_scale` in `data_enemies.gd`: ghoul ×1.35, sentinel ×1.25, boss ×2.2 are already set; goblin/orc/ogre/wolf
  are modelled at true size (scale 1.0).

### 3.5 Verify visually (real renderer)
- `tools/render.sh --resolution 1600x900 res://tests/tools/capture_enemies.tscn -- --out=<dir>` — the first capture
  was taken while models were still scrambled (enemies stayed standing after death). Re-run it and confirm bodies
  fall, pools are visible (decal placement was fixed after that capture), and decay reads. The run takes > 10 min
  on software Vulkan; run it in the background.
- Add a `capture_interiors` tool (load each interior, render the `room` view) and a town top-down render to check the
  new lots and that no NPC floats.

### 3.6 Known issues from the builders (worth a pass later)
- `aether_sentinel`: two-handed library clips make the shield hand grab the maul (needs one-handed heavy clips).
- `grave_archer` / `bandit_marksman`: no arrow in the drawing hand; bowstring is static.
- `shade_stalker`: very dark at distance by design — consider a faint violet rim while stealthed.
- Weapon bones: `weapon.L/R` are non-deforming in `bh_skeleton.py`; builders worked around it per module with a
  `finish_mesh` hook. Cleaner: handle it once in `build_chars.build_character`.
- Builder helper code lives inside character modules (`enemy_hollow_soldier.py`, `enemy_bandit_cutthroat.py`,
  `town_matron.py`, `town_elder.py`) — don't delete/rename them; consider moving the helpers to shared `bh_*.py` files.
- `anim_meta.json` has not been regenerated with the new clips (`death_back`, `death_fwd`, `death_crumple`, `devour`);
  the game reads real clip lengths from the models, but run `python3 build.py -- meta` for completeness.

---

## 4. Definition of done for the next run
- No floating or sunk NPCs anywhere (test + render).
- All 8 interiors enterable and exitable from the matching doors; repeated in/out cycles leave no duplicate
  players/NPCs/maps (door cycle test).
- 13 new NPCs present with lore-rooted dialogue; guild join/promotion and the inn are reachable in play.
- Suite green, captures inspected, changes committed and pushed to `update-0.01-q1u5d0`.
