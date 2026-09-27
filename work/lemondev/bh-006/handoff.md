# bh-006 handoff — loot pickup fix, auto-loot, 3D item models, sparkle drops, consumables + Town Portal, weapon roster, weight

Status: IMPLEMENTED — UNVERIFIED (benchmark gate): all component and integration checks below passed with current
evidence; no commercial benchmark capture was available, so the blind A/B benchmark gate is unverified (disclosed in
the contract). Nothing is committed (user rule: work on main, uncommitted).

Scope and revision: working tree on `main` on top of 07244e8 + the earlier uncommitted bh-004/bh-005 work.

## What changed and where

| Area | Files |
|---|---|
| Pickup fix | `src/autoload/loot.gd` (`landing_point`, `floor_under`: drops land on walkable ground near the corpse, never on wall/tree tops or behind colliders), `src/actors/player/player.gd` (`interact_distance` flat with 1.6 m height tolerance, `find_interact_target` prefers loot, R re-scans immediately) |
| Auto-loot | `src/autoload/settings.gd` (`auto_loot_enabled` + filter `auto_loot_mode`), `src/ui/hud/hud.gd` (`_build_side`: checkbox, load meter, portal chip + Dispel, left of the HP orb), `settings_window.gd`; `loot_drop.gd` magnet pickup |
| Ground loot | `src/loot/loot_drop.gd` (own model, glint overlay, ground glow, sparkles; no beams), `src/vfx/loot_fx.gd` (shaders), `src/loot/item_models.gd` (instancing, lay-flat, min size, bounds) |
| 3D models | `tools/blender/items/*` -> `game/assets/items/*.glb` (164 bases + gold pile), icons `game/assets/ui/icons/items3d/*.png` (70 new bases) |
| Weapons | `data_weapons.gd` (greataxe, javelin, club, claw, knuckles), `data_items.gd` (`ROSTER` 50 weapons, DPS-budget damage; own attack speed + weight for the old 24), `weapon_loadout.gd` (`aps()`), `equipment.gd`, player/tempo attack rate, javelin projectile (`projectile.gd` "model:" look), classes/tempos/shops lists, held model = item model (`Player.weapon_model_for`) |
| Weight | `item_base_def.gd` (`weight`, `attacks_per_second`, `model_path`), `DataItems.default_weight`, `Inventory/Equipment/ItemInstance.weight()`, `HeroData.carried_weight` -> `StatCalculator` (capacity 55 + 1.6·STR, +0.2% move speed per STR, slowdown from 35% load up to 30% at 100%, Overburdened 45% slower + no dodge / dash skills), boots move-speed implicits, inventory load bar, tooltips, character sheet |
| Consumables | `data_items.gd::_consumables` (20), `status_rules.gd` (12 elixir buffs), `player.gd` (buffs, throwables via `Lob.throw_node`, Phoenix Feather on death), potion belt order, shop stock, monster drops (`ItemGenerator.random_consumable`) |
| Town Portal | `src/world/town_portal.gd` (tear -> vortex shaders, inflow particles, return portal in town, dispel/expire/replace), `game.gd` (`travel_to_point`, spawn on map load), `hero_data.gd` (saved) |
| Also fixed | HUD buff/debuff icons never drew (`UIArt.status_icon` doubled the path); level-up / enemy heal / Tempo heal beams were never freed (permanent pillars) -> `VFXLib.beam_flash` |

## Setup / launch
Open `game/` in Godot 4.7.2 and play. Quick start into the forest: `Godot.exe --path game -- --class=knight --map=ruined_forest`.
Controls: R interact / pick up, Auto-Loot checkbox beside the HP orb, Town Portal Scroll from Tovin's Provisions
(right-click / use), Dispel button on the HUD chip.

## Gate results (all on this revision)
- Component tests: `Godot.exe --headless --path game res://tests/run_tests.tscn` -> TOTAL 9451 checks, 0 failures
  (15 suites; new `test_loot.gd` 17 tests / 1128 checks) — `evidence/tests_summary.txt`. Baseline before the run: 8279 checks, 0 failures.
- Compile: `-s res://tests/tools/compile_all.gd` -> 191 scripts, 0 failed (`evidence/compile_all.txt`).
- Runtime regression: combat bot knight + mage, ruined_forest 60 s: ok, 0 deaths, drops spawned, no script errors
  (`evidence/playtest/combat_*.json`).
- Rendered integration (real renderer, 1920x1080, knight L34): `res://tests/tools/capture_loot.tscn`
  -> `evidence/captures/01..11*.png` (drops per rarity, auto-loot, weapons in hand + javelin throw, inventory load +
  tooltip, portal tear/opening/open/close-up, return portal in town).
- Performance (this PC, vsync on, 1920x1080, 240 frames, final capture run): 15 drops + gold on screen avg 16.58 ms,
  p95 17.87, worst 33.91 (single missed vsync frames); Town Portal open avg 16.55 ms, p95 17.52, worst 33.38
  (`evidence/captures/perf.txt`). An earlier run of the same scenes had worst 17.89 / 17.65 ms. Other scenes not measured.
- Models: 165 GLBs import in Godot 4.7 without errors; contact sheets `evidence/sheet_*.png`.
- Independent critic: see "Review" below.
- Blind benchmark: UNVERIFIED (no commercial reference supplied/captured).

## Deviations / notes
- Weight acceptance relaxed during the build (see contract Amendment): equipment >= 4x the median non-equipment unit
  and >= 10x on average, instead of >= 3x the heaviest non-equipment unit.
- New weapon types reuse existing clips (no new animations): great axe = greatsword set, club = axe set, claw and
  knuckles = dagger set, javelin = wand throws + spear heavy.
- Existing items keep their SVG icons; new items use icons rendered from their models.
- Auto-Loot defaults to off (matches the old behaviour where only gold was collected); the filter now means
  "which drops", the checkbox is the switch.

## Review (lemondev loop)

| Component | Pass | Reviewer | Verdict | Single largest gap | Result |
|---|---|---|---|---|---|
| bh-006 batch | 1 | fresh critic #1 (evidence only) | REJECT | Town Portal vortex opened inside scenery (waypoint pillar / town brazier): placement tested a thin line only | fixed: `find_clear_spot` cylinder clearance + LOS + landmark distance, refuses when cramped; designed `town_portal` marker on the terrace; tests `test_portal_never_opens_inside_scenery`, `test_return_portal_stands_on_its_terrace_spot`; recaptured 09/10/11 |
| bh-006 batch | 2 | fresh critic #2 (no prior context) | PASS | hard seam in the vortex shader (angular noise not periodic at +-pi) | fixed: all angular noise sampled on the circle; recaptured 10 (no seam) |

Pass-1 also asked for missing evidence, now present: loot preferred over a nearer door, dodge blocked at full load
(tests), character sheet load (06c), inventory load bar (06a), compile output. Minor items reported by critic #2 and
their status: nameplate hidden by the rim (raised above the vortex — fixed); inventory load one change behind the
HUD (recomputed on refresh — fixed); the inventory window covers the HUD Auto-Loot checkbox while it is open (left as
is: windows sit above the HUD); two Elite items shared the random rare name "Ash Grasp" (pre-existing rare-name
generator, out of scope). The seam fix itself was verified by capture only (no third critic run).
