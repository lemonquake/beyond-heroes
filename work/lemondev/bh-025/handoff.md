# BH-025 — Music system, recorded themes and weapon sounds

State: **IMPLEMENTED — VERIFIED BY TESTS AND A LIVE PROBE IN THE GAME'S RENDERER.** Nobody has listened to it: the run
had no way to hear audio, so levels and the synthesised sounds were checked by measurement only.
Baseline: `main` fast-forwarded to `5ade074` (BH-024). Engine: Godot 4.7.2.

## What was asked

1. Bring the local tree up to date.
2. A music system from the files in `audio/`: `main_theme.mp3` the default, music at 60 % unless the player changes
   it, the recorded weapon and hit sounds in use, other effects created, `aljay_theme.mp3` when Paul David speaks of
   Aljay and Roydo.
3. Push to main, build the EXE and the APK.

## What was done

- `main` had nothing new on `origin/main`; BH-024 sat unmerged on `origin/lemonquake/zealous-gates-mysgx9`, one
  commit ahead. `main` was fast-forwarded to it.
- `Music` autoload (`game/src/autoload/music_director.gd`); what plays where, the layers, the volume rule and the
  sound table are in `docs/MUSIC.md`.
- `tools/audio/import_pack.py` (pack -> game), 22 new recipes in `tools/audio/sfx_bank.py`.
- `models/special_weapons/` (the models BH-024 was waiting for) is committed as it was found; the weapons themselves
  are still to be built (docs/SPECIAL_WEAPONS.md).

## Evidence

- `game/tests/unit/test_bh025.gd`: 13 tests, 760 checks, 0 failures.
- `game/tests/tools/probe_bh025.tscn` in the real renderer, 13 of 13: town and road play main_theme; a fight on the
  road brings battle_theme and the road's music resumes where it stopped; Battle Music off keeps the road's music;
  Paul David's small talk keeps Olivar's music, "And Roydo?" brings aljay_theme, his tale keeps it, the town's music
  returns afterwards; Emberforge Depths plays fire_dungeon_theme. Screenshots in `evidence/`.
- Full suite: the suites that fail are the ones BH-024's handoff lists as failing on its baseline, with the same
  counts (test_balance 14, test_bh016 14, test_bh017 1, test_enemies2 8, test_inventory_overhaul 15).

## Limits

- Not listened to. The three stingers and the synthesised hits in particular want a human ear.
- The boss and battle layers on a multiplayer client standing on the host's map rely on blows traded (replicas have
  no AI state); that path has no test.
- The pack's origin and licence were not supplied; `ASSET_CREDITS.md` says so.
- The recorded themes are tracked twice (`audio/` and `game/assets/audio/music/`, 25 MB each).
- `test_perf` did not finish inside the run's time limit and was not judged.
