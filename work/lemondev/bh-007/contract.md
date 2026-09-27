# bh-007 contract — Olivar, Wyman Outpost, crafting, ingredient drops, minibosses, stage clears

Run id `bh-007`, 27 September 2026. Engine Godot 4.7.2 (Jolt, Forward+), Windows 10, RTX 4060. Branch `main`,
uncommitted working tree (user rule). Baseline: HEAD b016083, test suite before the run in `evidence/baseline_tests.txt`.

## Request (user, verbatim intent)
Expand the maps around the first stages. Two safe zones near Malasugue:
- **Olivar** — a small town selling more advanced but more expensive equipment; the stock cycles every time the
  player clears a stage or a miniboss.
- **Wyman Outpost** — a hero camp: hero NPCs whose levels and tiers you can see, a checkpoint where you rest, item shops.
- **Item crafting**, and **ingredient drops** from enemies. "Improve every aspect, do more."

## Components (one owner each; interfaces in brackets)
| # | Component | Files | Acceptance |
|---|---|---|---|
| C1 | Ingredients + recipes + crafting rules | `data_items.gd` (materials), `data_recipes.gd`, `core/crafting/crafting.gd` | pure model; every recipe's inputs/outputs exist; craft consumes exactly, refuses when short/full/unknown/wrong station; learned recipes persist |
| C2 | Crafting window + stations | `ui/windows/crafting_window.gd`, `world/crafting_station.gd`, dialogue service `crafting_*` | readable at 1920×1080 and 1280×720; have/need counts; craft ×1/×5; variants; locked recipes explain how to learn |
| C3 | Enemy ingredient drops + herb gathering | `data_enemies.gd` loot, `world/gather_node.gd` | every enemy family drops at least one ingredient; nodes give herbs, deplete, regrow |
| C4 | Stage clears + minibosses | `data_minibosses.gd`, `spawner.gd`, `enemy.gd`, `loot.gd`, `hud/stage_tracker.gd` | clearing every camp of a combat map fires `stage_cleared` once per visit; minibosses are named, stronger, drop a trophy + Elite gear, respawn after a cooldown |
| C5 | Olivar | `maps/olivar.gd`, `data_npcs_olivar.gd`, shops | premium stock (Advanced floor, higher item level, higher markup) rerolls exactly when the hero's clear counter moves |
| C6 | Wyman Outpost | `maps/wyman_outpost.gd`, `data_npcs_wyman.gd`, `ui/windows/hero_roster_window.gd`, checkpoint | hero NPCs show level/tier/guild; roster board; bonfire rests free + sets checkpoint; respawn offers the checkpoint |
| C7 | Island integration | `data_island.gd`, `data_maps.gd`, `westreach.gd`, atlas art, docs | new roads walkable on the navmesh, links tested, loop Mill→Olivar→Wyman→Fields→Mill |
| C8 | Item art | `tools/blender/items`, icons | every new base has a model + icon |

## Gates
- Headless suite on 4.7.2: 0 failures; new/extended tests for C1–C7 (island tests include the new maps).
- `compile_all`: 0 failed.
- Real renderer captures (1920×1080) of both places, crafting, roster, stage clear, miniboss, the M map.
- Frame time on each new map (walk, vsync on): report avg / p95 / worst; target p95 ≤ 16.7 ms on this PC.
- Blind benchmark: no commercial capture supplied → **UNVERIFIED** unless the user supplies one. A fresh critic will
  judge the evidence packet (PASS/REJECT, single largest gap), max 8 passes.

## Invariants
- No Filipino words/names (user rule). Olivar and Wyman are the user's names. New names are provisional (LORE §6b).
- Old saves load (new hero keys optional). Map ids `sanctuary`/`westreach` unchanged.
- Never kill Godot by image name; only the PID started here.
