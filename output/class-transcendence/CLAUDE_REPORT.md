# Class Transcendence (bh-036): report

Implemented over three sessions (2026-10-03/04) on `main`, Godot 4.7.2. Player-facing description:
`docs/CLASS_TRANSCENDENCE.md`; changelog entry BH-036 in `docs/CHANGELOG.md`. Network protocol 20.

## What is in

- **Sixteen classes**: Knight > Royal Guard > Dark General / Grand Paladin; Hunter (saved id `ranger`) > Tracker >
  Wildwarden / Starstrider; Mage > Arcanist > Archmage / Void Sovereign; Shadowblade > Nightstalker > Phantom Reaper /
  Blood Sovereign. Registry `game/src/data/data_transcendence.gd`, state and validation
  `game/src/core/progression/class_transcendence.gd`, flow `transcend_flow.gd`.
- **Advancement** at 60 and 120 through Grand Master Edran Vale in every Guild House (no guild needed). Heroes at 121+
  can take both steps at once. Each step grants 3 skills and 3 talents at rank 1 as free ranks that respec never
  refunds. A corrupt or forged path falls back to the longest valid prefix.
- **36 skills, 36 talents** (`data_transcendence_skills.gd`, `src/skills/transcend_skills.gd`, `transcend_zone.gd`,
  `snare_line.gd`), each with its own icon, plus 12 signature traits (`src/actors/hero/class_signature.gd`).
- **Equipment rules**: one evaluator (`src/core/items/class_requirements.gd`) for the kinds any / family / lineage /
  exact. Every one of the 975 bases has a readable rule (any 453, family 486, exact 24, lineage 12). Unbound skips
  level and attributes but not the class rule. Tempo permissions are unchanged.
- **36 new pieces** (`data_transcendence_gear.gd`): a weapon, armour and accessory per class. Sold by the Grand
  Master's Armory (Elite) and found as loot from level 60 or 120. Each has its own 3D model and icon. The 12 armours
  are distinct worn class armour (`tools/blender/hero/hero_wear_transcend.py`).
- **Multiplayer**: other players see the current class, in its colour, on the existing line beneath the name. The
  server validates the path, and the class shows only after the official save is acknowledged.
- **Change from the brief, by the user**: no master glows or auras. The user had all glows removed; classes are told
  apart by their armour instead.

## Evidence (all under `output/class-transcendence/`)

| Area | Files |
| --- | --- |
| Catalogues | `class_catalogue.json`, `gear_requirements.json` (written by `tests/tools/transcend_export.tscn`) |
| Balance | `balance.csv`, `balance_report.md`, `balance_retune.csv` (levels 121/300 after the last tuning pass) |
| Focused tests | `tests/*.log`: test_transcendence (19 tests, 4250 checks), _signatures (18), _skills (12), _net (5), all passing in their last runs; `tests/server_tests.log` (45 server tests OK) |
| Custom multiplayer, 2 real clients | `net/`: same-session advancement, forged claim refused, re-dress, map change, reconnect (PASS both sides) |
| Official accounts, 2 real clients | `official/`: import at 121, ack before display (+101 ms ack, +114 ms seen by B), late join, map change, reconnect, sibling switch refused |
| Screens | `screens/` (1920x1080), `screens_1280x720/`, `screens_touch/`, `armor/` (front and back of all 12 armours) |
| Regression | `regression/tests_final.txt` |

## Regression

Full suite, 2026-10-04: 59 test files run before it was stopped on request, so the remaining files (including the
transcendence suites) were not re-run in this pass; their earlier runs are in `tests/`. Failures in the 59:

- test_balance: 6 of 16 checks. This is the known baseline (5 failures on the pre-feature baseline in
  `baseline/tests_full_summary.txt`), and its power band varies about ±10% between runs.
- test_bh028_arena: 1 check (the pre-feature baseline had 2).

These had failed earlier in this work and pass now: test_loot (new item models and icons), test_bh016, test_bh024,
test_bh030 and test_bh031.

## Open items

- World-host handoff with transcended heroes was not run as its own probe. The class rides on the player profile,
  which handoff does not touch.
- The 12-player crowd frame-time comparison (`tests/tools/transcend_crowd_perf.tscn`, class armour vs plain armour)
  is written but was not run.
- There was no Android device for a performance check. Touch layouts were checked on desktop (`screens_touch/`).
- The official server must be updated together with the game (protocol 20).
