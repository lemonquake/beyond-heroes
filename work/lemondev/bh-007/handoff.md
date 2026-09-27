# bh-007 handoff — Olivar, Wyman Outpost, crafting, ingredient drops, champions, stage clears

Status: **IMPLEMENTED — UNVERIFIED (benchmark gate only).** Every component and integration check below passed on the
current revision, and a fresh critic passed the evidence on review pass 4. No commercial benchmark capture was
available, so the blind A/B benchmark gate is unverified (disclosed in the contract). Nothing is committed (user rule:
work on `main`, uncommitted). Revision: working tree on `main` over b016083.

## What the user gets

| Area | What changed | Main files |
|---|---|---|
| **Olivar** (new map `olivar`) | Walled lake-trade town east of the Old Mill: plaza with the Founder's statue, Ashby's Arms Exchange, Crane's jewel stall, Pell's Apothecary + alchemy table, docks and pier, Lake Terrace waypoint, 6 townsfolk. **Premium merchants** (Advanced floor, item level +3, Elite/Master/Mythical odds that grow with level, 1.8–1.9× markup) that **restock exactly when the hero's clear counter moves** (stage clear or champion kill), never on a timer. | `src/world/maps/olivar.gd`, `data_npcs_olivar.gd`, `data_shops.gd`, `core/shops/shop.gd` + `shop_def.gd` (`restock_on_clears`, `ilvl_bonus`, `rarity_weights`) |
| **Wyman Outpost** (new map `wyman_outpost`) | Hero camp above Reedwater Marsh: bonfire **checkpoint** (free full rest, Tempos restored; after death "Wake at Wyman Outpost"), **8 hero NPCs** with level · tier · guild plates and tier emblems who spar, cast and patrol, **Hero Register** window (all heroes + your rank + next promotion), quartermaster and field-kit shops, field forge, workbench, camp kettle, training yard, watchtower, Marsh Overlook, waypoint. | `maps/wyman_outpost.gd`, `data_npcs_wyman.gd`, `world/camp_bonfire.gd`, `world/roster_board.gd`, `ui/windows/hero_roster_window.gd`, `npc/npc.gd` (hero plates, weapons, activities), `game.gd` + `pause_menu.gd` (checkpoint respawn) |
| **Crafting** | 30 recipes at 3 station kinds (forge, alchemy, workbench): draughts, tonics/wards, bombs, scrolls, refined stock, charms, and **gear with a chosen kind** (Tempered = Advanced, Champion's = Elite, Aetherforged = Master; always fine quality, marked Crafted). 8 **recipe scrolls** (Olivar + champion drops). **Salvage** tab (gear → iron/hide/linen + dust/motes by rarity). Stations: Brannoc's Anvil (Malasugue), Pell's table (Olivar), Wyman's forge/workbench/kettle; NPCs open them too. | `data/data_crafting.gd`, `core/crafting/crafting.gd`, `ui/windows/crafting_window.gd`, `world/crafting_station.gd` |
| **Ingredients** | 17 new materials: 10 monster parts, 4 herbs, 2 refined, Champion Essence. **Every enemy family drops at least one** (e.g. wolves → Wolf Fang, goblins → Fire-pot Resin, orcs → Orc Tusk). **Herb patches** (pick, regrow after 5 min, remembered across loads) in Westreach, the Ruined Forest, Olivar and Wyman. Tooltips list "Used in: …". | `data_enemies.gd` loot tables, `world/gather_node.gd`, `ui/widgets/tips.gd` |
| **Champions & stage clears** | 6 named minibosses (Snagtooth, Greymaw, Rook Hallister, Warchief Karg, Grundle the Chained, the Ossuary Keeper): tougher than elites, gold ring/ember crown/rim, HUD bar, 2-line plate, Elite gear + Champion Essence + 35% recipe scroll, return 10 min after defeat. **Stage clear** = every camp of a combat map in one visit: banner, XP + purse, counts for Olivar. HUD **stage tracker** (camps x/y, champions here/defeated/back in n min). Bard Pip in Olivar reports every champion's status. | `data_minibosses.gd`, `spawner.gd`, `enemy.gd`, `enemy_bar.gd`, `loot.gd`, `ui/hud/stage_tracker.gd`, `hud.gd` |
| **Island** | Lake Shore Road planked over to Olivar; new **Fen Road + Fen Bridge** to Wyman; Watch Road Olivar↔Wyman → a walkable loop Mill→Olivar→Wyman→Fields→Mill. Two new network waypoints. Atlas repainted with both settlements; M map routes to them. Westreach 15 m wider east. | `data_island.gd`, `data_maps.gd`, `westreach.gd`, `ruined_forest.gd`, `tools/ui_art/salmonan_atlas.py`, `settlement_builder.gd` |
| **Also fixed / added** | Ground **loot name tags** were never drawn (setting existed, no code): now drawn, stacked, hover + click to pick up. Stale pickup prompt after travel. Shop footer hint clipped by the frame. Field Guide "First steps" gained Craft / Stages entries. | `ui/hud/loot_labels.gd`, `hud.gd`, `shop_window.gd`, `guide_window.gd` |
| **Art** | 25 new item models + icons (Blender pipeline), atlas settlements. | `tools/blender/items/item_goods.py`, `item_kit.py`, `game/assets/items/*.glb`, `assets/ui/icons/items3d/*.png` |
| **Docs** | LORE §6b (Olivar, Wyman, people, champions, crafting), MAPS.md (new maps, boundaries, loop). | `docs/` |

## Setup / launch
Open `game/` in Godot 4.7.2 and play. Quick starts (a spare save slot):
`Godot.exe --path game -- --class=knight --slot=96 --map=olivar --level=8` or `--map=wyman_outpost` or `--map=westreach --spawn=fen_road`.
From a normal save: open the South Gate (Captain Hald), then the Lake Shore Road east from the Old Mill, or the Fen Road east from Lantern Fields.

## Gates (current revision)
- Tests (4.7.2 headless): **10,801 checks, 0 failures** (baseline 9,451). New `tests/unit/test_crafting.gd` (603 checks); `test_island` now covers the new maps (755 checks; its ground probe was made map-accurate and bridge-aware). `evidence/tests_final.txt`.
- Compile: 209 scripts, 0 failed (`evidence/compile_all.txt`).
- Real-game captures, real renderer: `evidence/final3/*.png` + `report.json` (1920x1040 window); `evidence/ui720/*.png` (forced 1280x720 window).
- Frame time (vsync, standing view, 240 frames): Olivar avg 16.6 / p95 17.8 ms, Wyman 16.6 / 17.8, **Malasugue baseline 16.7 / 17.6** → parity. An A/B of the last commit vs this tree in Malasugue also showed parity (`evidence/perf_ab.txt`). The contract's ≤16.7 ms p95 is missed by ~1 ms on every map including the untouched baseline (vsync jitter on this PC).
- Blind benchmark: **UNVERIFIED** (no commercial reference).

## Review loop (fresh critic each pass)
| Pass | Verdict | Single largest gap | Fix |
|---|---|---|---|
| 1 | REJECT | Combat side not visible: champion indistinct, no capture of champion or enemy loot | Champion ring/ember crown/rim/light + 2-line plate; **loot name tags implemented** (were never drawn); captures 16/17/17b |
| 2 | REJECT | 720p evidence invalid (window size restored from settings) | `--win=` forces the window; resolution recorded in report.json |
| 3 | REJECT | Hero Register clipped its 9th row and your row | Compact rows, shorter intro, footer margin; no banner over champions |
| 4 | **PASS** | — | Minor notes below |

## Known minor issues (not fixed)
- Olivar's interior reads thinner than Malasugue from high overview angles (open lawns between houses).
- World labels can overlap each other or the talk prompt in crowded spots (camp yard).
- Some thin weapon icons (spears/javelins, from bh-006) are hard to read at slot size.
- Stage clears can be farmed by re-entering a map (by design: the user asked for a restock on every clear).
- The miniboss scale-up relies on the base model; no unique champion models.

## Next smallest actions
1. Decide whether to commit (ask the user). 2. Dress Olivar's lawns (garden plots, carts, a second market row). 3. Unique champion models or at least tint/accessories.
