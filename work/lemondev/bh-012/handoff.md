# bh-012 handoff — Dungeons, 25 monsters, gacha gear names and stars, Relic Caches, Tempo summoning, new passives, road camps

Status: **IMPLEMENTED — mechanics verified by tests and in-game captures; blind benchmark review against the user's
reference UNVERIFIED** (no independent critic was run). Work is uncommitted on `main` (house rule).

## What changed
| Area | Change | Files |
|---|---|---|
| **Dungeons** | 5 themed dungeons × 4 floors = 20 maps built by one builder from ASCII floor plans: storeys at 0/4/8 m joined by stair flights, galleries with parapets over the halls below, luminous basins (water / spore bog / lava / frozen / void) with bridges on arches, themed stone, lights and dressing. Floors 1–2: an elite Seal Keeper pack seals the descent portal; floor 3: the dungeon champion holds it; floor 4: the boss sanctum (the boss returns after 20 min; first clear sets the dungeon's flag). Broken seals persist; the surface gate offers every reached floor; deeper up-portals can leave the dungeon. Treasure chests (coffer / gilded / hoard) refill after 30 min. | `data/data_dungeons.gd`, `world/maps/dungeon.gd`, `world/dungeon_runtime.gd`, `world/treasure_chest.gd`, `world/teleporter.gd`, `world/material_library.gd`, `world/map_builder.gd` |
| **Gates on the island** | Hollowroot Warren (Westreach, off the Fen Road), Saltmouth Deeps (the smugglers' sea cave), Emberforge Depths (above the Lake Shore Road), Rimeglass Barrow (Ruined Forest north-west rim, new Rime path), Shattered Orrery (Wyman Outpost, new Brass path corridor). Places, trails and links in the island data (M map, routes). | `data_island.gd`, `westreach.gd`, `ruined_forest.gd`, `wyman_outpost.gd` |
| **25 monsters** | 4 per theme + 5 bosses, each with its own model (builders A–E, Blender) and stats/attacks/traits: e.g. boat-hook pulls, tide lances, shelled crabs, anchor-chain hauls, spore-popping sporelings, charging boars, root snares, blinking imps, fire-breathing hounds, furnace-shield thralls, lava golems, shattering husks, frost wraiths, freezing web spiders, war-crying jarls, crossbow sentries, self-destructing Starmotes, blinking duelists, gravity-well seers; bosses with 3 phases, summons, pools and ring novas. Five named champions. | `data/data_enemies_dungeon.gd`, `data_minibosses.gd`, `enemy.gd`, `enemy_traits_ext.gd`, `character_visual.gd`, `game/assets/characters/*.glb` |
| **Gacha gear** | Licensed+ gear gets a unique proper name + epithet ("Fenenvex, Hide of Frostguard"), 1–5 stars from its rolls ("Perfect rolls" badge), a five-star drop flourish; names/stars on tooltips and ground labels. Relic Caches (Worn/Gilded/Radiant) with a card-flip reveal; every piece at least Advanced/Elite/Master. | `core/items/item_names.gd`, `item_generator.gd`, `item_instance.gd`, `relic_cache.gd`, `ui/windows/gacha_reveal_window.gd`, `tips.gd`, `loot_drop.gd` |
| **New passives** | Affixes: Gold Find, Experience, +% HP / Mana regeneration, Life / Mana on Kill, Potion Effectiveness, Thorns, damage to Champions, Soul Ember Find, Tempo Damage; 10 relic passives (stat bundles) on some Licensed+ gear. | `data/data_relics.gd`, `stat_calculator.gd`, `stat_defs.gd`, `actor.gd`, `player.gd`, `loot.gd`, `tempo_rules.gd` |
| **Tempo summoning** | Soul Embers (drops; far more in dungeons), 10 per call / 90 per ten-call, 3★/4★/5★ with pity (4★ every 10, soft pity from 50, hard at 70), a daily featured renowned spirit (50/50 with guarantee), 5 new summon-only renowned spirits, Resonance I–V for duplicates, the Spirit Hall (bind / swap / rest / release for embers), a 100-ember welcome gift, ember purchase for gold. | `core/tempos/tempo_gacha.gd`, `data_tempos.gd`, `tempo_data.gd`, `hero_data.gd`, `tempo_caller_window.gd` |
| **Road camps** | 8 new Westreach camps along the Lake Shore Road, Mill Lane, Fen Road, Field Road and Coast Road (bandits, dead, goblins, wolves, dungeon spill); an orc band on Wyman's Brass path; a Rime spill in the Ruined Forest. "Wild" camp support for town maps. | `westreach.gd`, `wyman_outpost.gd`, `ruined_forest.gd`, `spawner.gd` |
| **Guide** | Field Guide page "Dungeons & Relics". | `guide_window.gd` |
| **Assets** | 27 dungeon props + 4 texture sets (Builder F); 9 item models + icons. | `tools/blender/environment/assets_dungeon.py`, `tools/textures/gen_textures.py`, `tools/blender/items/item_goods.py` |

## Evidence (`evidence/`)
- `dungeons/` — overview/arrival/goal renders of five floors (after the lighting pass).
- `captures/` — bestiary lineups per theme and each boss in game, fights on Deeps F2 and Ember F2, the Warren and Deeps
  gates, Relic Cache sealed/revealed, summon page, ten-call reveal, Spirit Hall, named-gear tooltips and ground labels.
- `models_*/`, `env_kit/` — builder evidence (contact sheets, scratch Godot import checks).
- `validate_plans.py` — plan validator (20/20 floors OK).
- `tests_final.txt` — full suite: **17,524 checks, 19 failures**, all in `test_balance` (stochastic class bands), `test_enemies` (roster count, now 53) and `test_enemies2` (8 checks) — the same suites that fail on the untouched baseline (bh-011: 15,760 checks, 20 failures). New `test_bh012`: 11 tests, 1,142 checks, 0 failures. compile_all: 0 failed.

## Not verified / known
- Blind A/B benchmark against the user's reference image: UNVERIFIED (self-review only).
- Performance on phones not measured for the dungeon floors (desktop only); the floors use the existing kit batching and
  efficiency-mode paths.
- Builder-noted model limitations (rigid capes/halos clipping in some poses, staffs dipping into the floor in deaths).
- Ember floors remain dark and red-heavy by design; tune `THEMES.ember` if needed.
