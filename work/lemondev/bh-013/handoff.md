# bh-013 handoff — Dungeons on the map, 15 new dungeons, raid recovery, 21 new monsters, push + APK

Status: **IMPLEMENTED — mechanics verified by unit tests and in-game captures; blind benchmark review UNVERIFIED**
(no benchmark supplied). Committed and pushed to `main`; debug APK rebuilt to `build/BeyondHeroes.apk`.

## What changed
| Area | Change | Files |
|---|---|---|
| **Map (M)** | Every dungeon gate is a public place from the start, drawn with the arch icon, name, level range and difficulty stars on the Island/Local views; the sidebar shows difficulty, floors, lord, champion and raid state. The Underground tab lists all 20 dungeons (plus the Catacomb chain) as a grid: stars, tier, levels, floors, and Unexplored / Floor n of N / Raided — returns in m min / Recovered · held by the Usurper. Search and Directions reach every gate (mid-road junctions `on_road`). | `ui/widgets/atlas_view.gd`, `ui/windows/world_map_window.gd`, `data/data_island.gd`, `world/island/route_planner.gd` |
| **15 new dungeons** | Cutpurse Cellars, Gnashgut Burrows, Blackvault Ossuary, Ironjaw Warcamp, The Waxen Hive, Blackwater Sump, Briarheart Hollow, Dunemourn Tomb, Thunderwell Spire, The Umbral Undercroft, Prismdeep Geode, The Gilded Vault, Twinspire Reliquary, Wyrmcoil Caverns, The Maw Beneath — levels 2 to 58, tiers 1–5 (Easy…Mythic), 2–5 floors, 11 new themes. Floor plans generated offline and validated (`tools/dungeon_gen/gen_plans.py` → `data_dungeon_plans.gd`). Gates in Westreach, the Ruined Forest and Olivar with trails. | `data/data_dungeons_x.gd`, `data/data_dungeon_plans.gd`, `data/data_dungeons.gd`, `world/maps/dungeon.gd`, surface map scripts |
| **Raid recovery** | The boss's death records a raid per hero (`hero.dungeon_raids`, wall clock): 30–120 min by tier (tier 1 ≈ 30–55, tier 5 ≈ 105–120). While recovering, camps and Seal Keepers do not spawn; the floor champion and the sanctum's **Usurper** (a named miniboss per dungeon) still come back on their own timer; the boss never returns once raided. Afterwards every camp replenishes. | `data/data_dungeons.gd`, `world/dungeon_runtime.gd`, `world/spawner.gd`, `core/hero_data.gd` |
| **21 new monsters** | Gravecaller (summons Bone Thralls that crumble with it), Riftcaller (opens a Void Rift that spawns shades), Mirage Weaver (mirror images, swaps places), Bloodbinder (draining tether, broken by range/line of sight), Aegis Acolyte (links an ally: 85% less damage), Storm Herald (delayed bolt runes, Static → stun), Mirror Knight (reflecting guard), Warband Chieftain (rally; its death breaks the band), Soulbound Twin (rekindles its fallen twin), Briar Lasher (thorn hide, vine pull), Broodhost (sheds Leechlings), Goblin Sapper (proximity mines), Treasure Gremlin (flees, sheds gold, escapes in 25 s), Gloam Ooze (splits twice), Tunnel Maw (burrows, erupts under you), Stonegaze Basilisk (petrifying gaze), Shellback Grinder (armored roll; flip it), Waxen Hive (nest), Hive Drone, Gloomwraith (ethereal phases), Prism Sentinel (sweeping beam). Helpers: Bone Thrall, Void Rift, Leechling, Mirror Image. 15 bosses (3 phases each) reuse the new models at boss scale. | `data/data_enemies_x.gd`, `actors/enemy/enemy_traits_x.gd`, `combat/sapper_mine.gd`, `actors/enemy/enemy.gd`, `core/combat/status_rules.gd` |
| **Models** | 21 new Blender-generated models (builders A/A2 casters, B1/B2 warriors+brutes, C/C2 creatures, D floaters). | `tools/blender/characters/enemy_*.py`, `tools/blender/creatures/build_*.py`, `game/assets/characters/*.glb` |
| **Fixes** | Floating creatures (wisps, wraiths, motes) were never animated — `_setup_floating` was never called; now hover/spin/pulse. Ground nests stay planted; the Void Rift's vortex turns. Dark themes (thorn, umbral, abyss) brightened. Hive trail re-routed along walkable ground. | `actors/character_visual.gd`, `data/data_dungeons_x.gd`, `data/data_island.gd` |

## Evidence (`evidence/`)
- `captures/` — map_island, map_gate_selected, map_local_westreach, map_directions_to_gate, map_underground; bestiary
  lineups (cellars, warcamp, sump, geode); bosses_1..5; new floors (fight_dg_*); new surface gates.
- `models_casters/`, `models_warriors/`, `models_brutes/`, `models_creatures/`, `models_floaters/` — per-model reports,
  rest/clip previews, scratch Godot import checks.
- `sites/` — gate-site search renders.
- `tests_final.txt` — full suite summary (see below).

## Tests
- New `test_bh013`: 11 tests, 1,017 checks, 0 failures — 20 dungeons/tiers/floors, gates public and routable, every
  new floor builds with portals and a boss spawn, recovery times per tier, raided floors empty / champion + usurper
  present / boss absent / camps back after recovery, save round trip, and each monster mechanic (summon caps + bound
  death, rift spawn/close, hive, parasites, split generations, images + swap, burrow untargetable, tether drain/heal/
  break, aegis link DR, static stun, mirror reflect, thorns, ethereal immunity/weakness, curl DR + flip, twin rekindle,
  rally + band break, gaze petrify, beam sweep, mine cap, gremlin escape).
- Full suite: remaining failures are the pre-existing baseline suites (`test_balance` stochastic class bands,
  `test_enemies` roster count, `test_enemies2`). `test_bh012` updated for the new rule (lords never return).

## Not verified / known
- Blind benchmark review: UNVERIFIED. Phone performance on the new floors not measured.
- Model limitations are listed per model in the evidence `.md` files (rigid back loads, curled-ball plate stretch, etc.).
- The starting town is still called "Malasugue" in data and UI (pre-existing name, not touched this run).
