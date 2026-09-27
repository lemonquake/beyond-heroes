# bh-005 handoff — starter Tempo, new-game guide, Tempo grades, renowned Tempos

State: **IMPLEMENTED — UNVERIFIED** (benchmark gate and independent blind review not run; see Gaps). Unit, live-AI,
data and rendered-UI evidence below is current for the final revision. Nothing committed (user rule: work on main).

## What changed
| Area | Files |
|---|---|
| Data: grades (Restless → Ascendant), classes Mystic (grade 2) + Warden (grade 3), 15 grade-gated skills, 5 renowned spirits with 6 unique skills, the starter Tobren | `game/src/data/data_tempos.gd` |
| Model: `grade`, `legend_id`, `mirror()`, `full_name()` (saved; older saves load as grade 1) | `game/src/core/tempos/tempo_data.gd`, `game/src/core/hero_data.gd` (roster grade) |
| Rules: `current_grade/next_grade/check_grade`, grade-aware `generate/refresh_roster/hire_cost`, `legend_data/legend_error/hire_legend`, `grant_starter`, legend ghost weapons | `game/src/core/tempos/tempo_rules.gd` |
| Actor: role AI (`ai`), data-driven dispatch (`use`), new handlers nova/bolt/chain/ward/rally/trap, execute + reset-on-kill, group heals; **fix**: projectile/blast callbacks no longer capture the Tempo (use-after-free crash when a Tempo was freed with arrows in flight) | `game/src/actors/tempo/tempo.gd` |
| New game: Tobren granted, guide opens once (`intro_guide_done`); level/deed raises the spirit grade and notifies | `game/src/autoload/game.gd`, `game/src/main.gd` (`--starter=0`, `--intro=1`) |
| Guide conversation with `{key:<action>}` placeholders | `game/src/data/data_guide.gd`, `game/src/core/dialogue/dialogue.gd` |
| Dialogue box without a world NPC, per-node speaker, services `field_guide`, `tempo_renowned` | `game/src/ui/windows/dialogue_box.gd` |
| Field Guide window (H): controls with live keys, Tempos/grades/renowned, first steps, replay intro | `game/src/ui/windows/guide_window.gd`, `ui_root.gd`, `input_setup.gd`, `settings_window.gd` |
| Shrine: grade status line, Renowned tab, grade badges; Tempo window/HUD frames show grade and share | `tempo_caller_window.gd`, `tempo_window.gd`, `tempo_frames.gd` |
| Veyra: grades and renowned dialogue | `game/src/data/data_npcs_town.gd` |
| Art: 20 skill icons, 2 crests, 6 portraits | `tools/ui_art/bh005_tempos.py` → `game/assets/ui/...` |
| Lore | `docs/LORE.md` §9 |
| Tests / tools | `tests/unit/test_tempos.gd` (+4 tests), `tests/unit/test_guide.gd` (new), `tests/tools/capture_onboarding.*` (new) |

## Evidence (Godot 4.7.2)
- Full suite: 8279 checks, 0 failures (`work/probe/full_run.log`); after the last UI fixes, the affected suites
  (tempos, guide, shops_dialogue, npcs): 4438 checks, 0 failures. `compile_all`: 185 scripts, 0 failed.
- `test_every_skill_works_live`: every skill of all 5 classes plus all 6 unique skills fired in a live map and produced
  its effect (damage / taunt / ward / rally / vault / smoke / heal; chain hit ≥ 2).
- Renders: `work/lemondev/bh-005/evidence/onboarding/01..17_*.png` (1920×1040 window client), art sheets
  `evidence/art_skills.png`, `evidence/art_portraits.png`.

## Gaps / next actions
- Benchmark gate UNVERIFIED: no commercial onboarding/companion reference evidence was captured.
- No independent critic pass; no 3840×2160 UI inspection; no FPS measurement.
- Balance untested in real play: grade prices (×1.6 … ×5), renowned prices 1.5k–12k, mirror 0.55–0.75.
- `test_npcs` took 658 s on the rerun (35 s earlier) while another Godot process was running — machine contention.
- Pre-existing uncommitted edits in player.gd, enemy.gd, fx.gd, damage_pipeline.gd, damage_result.gd,
  skill_runner.gd, vfx_lib.gd, character_visual.gd (mtime 04:07–04:32) were not touched by this run.
