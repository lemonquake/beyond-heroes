# Tempo, weapons, boss sets and cheats

State: **IMPLEMENTED — UNVERIFIED** under lemondev's complete acceptance protocol. Requested code, art, documentation and Windows/Android builds are implemented. Local checks below passed. Independent blind review and physical Android playtesting were unavailable; commercial superiority is not claimed.

Baseline: main at `8cde5d1`. Final source and asset hashes are recorded in `evidence/source-manifest.json`; package hashes in `evidence/builds.json`.

## Changes

- Tempo window fits the viewport, limits companion-tab icons, wraps headings, and scrolls its panes. Compact screens have Details and Your bag tabs; mouse and touch interactions remain available.
- Bows and crossbows require both hands. Equip, swap, companion equipment and legacy-save recovery preserve displaced items and prevent offhand shields or weapons.
- Ten new designs each for bows, crossbows, daggers, swords and axes; 21 existing bow models rebuilt. Crossbows have authored two-hand poses, normal/charged bolts, Ranger skill and shop/crafting integration.
- Fifteen complete boss collections: 187 individually obtainable pieces, 15 signature weapons and seven shields, worn geometry on every equipment slot, and matching rendered icons. Multiplayer avatars and character/Tempo previews display the equipped pieces.
- Actual level-30+ bosses, returning dungeon Usurpers and Depth Guardians drop exactly one random collection piece per reward bundle. Partial collections have 4x set-selection weight; missing pieces have 6x piece weight. Class affinity is 2x; all sets remain possible. Ownership includes the vault and companions. Ordinary loot remains alongside the single special piece.
- Set bonuses activate at 3, 6 and full collection. Boots retain the existing movement-speed convention. New weapon constructions have distinct speed/weight combinations.
- Added `asdf`, `lol`, `jjwp` and ten further cheats. The PDF and Markdown reference document all 19 existing and new codes.

## Validation

- Final focused suite: **50,618 checks, zero failures**, including equipment recovery, 10,000 projectile simulation steps, fast bolts against thin walls, 10,000 seeded set drops, complete-set equipment/bonuses/save behavior, item models/icons, animation hand contact, chat cheats, network wardrobe, and Tempo layout.
- Remaining regression groups: **30,143 checks, zero failures** (progression, shops/dialogue, skills, stats/status, team loot, Tempos and bridges).
- Isolated performance-settings suite: **243 checks, zero failures**. The unfiltered full-suite run stopped progressing after NPC tests and was terminated after more than five minutes without progress. Its partial log is retained; no full-suite pass is claimed. The pending groups were run separately.
- Baseline comparison at `8cde5d1` reproduces 25 existing failures in old skill-cap, Lape merchant and enemy tests. The class-power balance gate also has 15 failures matching the prior `output/depth-validation.log` failure categories. These unrelated failures remain; no global green test status is claimed. The 42 new catalog failures found during integration were corrected and the complete loot suite now passes.
- Tempo rendered checks: **50 checks, zero failures**, at 1920x1080, 3840x2160 and 1280x720, including touch, bag bottom, resize and empty states.
- All 15 worn sets inspected front/back. All 187 icons checked for nonempty alpha coverage. Blank first-pass icons were fixed by explicitly updating their render viewport.
- All 15 set-description panels fit 1920x1080; representative actual rendered descriptions inspected.
- Final live integration: **35 checks, zero failures**, including cold game boot, five weapon families, complete Truth of Raikuru, actual in-game Tempo window, three pause/resume cycles and 60 crossbow attacks.
- Final 60-second observation: 1920x1080, Vulkan Forward+, RTX 4060, Sanctuary, full Truth of Raikuru equipped. 8,633 frames, p95 **7.693 ms**, p99 **7.915 ms**, max **69.279 ms**, one frame over 16.67 ms. This is a desktop scene measurement, not a claim about all maps or Android performance. Background headless regression processes were running.
- Windows release export and Android debug export returned zero. Packaged Windows EXE cold-started cleanly. APK signature verified. No Android device was attached, so installation, touch behavior on hardware and device performance remain unverified.
- Two-page cheat PDF was rendered and visually inspected; generator validates that all 19 registered codes are documented.

## Reproduce

Use Godot 4.7.2 and the project's existing Windows/Android export presets. Open/import `game/project.godot` first. Run `res://tests/run_tests.tscn` headlessly with `-- --only=<suite names>` as recorded in the logs. Tests use hidden save slots, not the player's visible slots.

Asset sources: `tools/blender/items/build_artisan.py` (50 weapons and 21 bows), `boss_weapons.py` (signature weapons/shields), and `game/tests/tools/build_boss_set_art.tscn` (Godot gear export and icons, `-- --phase=gear` then `--phase=weapons`). Crossbow IK data comes from `tools/blender/characters/crossbow_poses.py`. Boss wardrobe geometry is authored in `game/src/actors/boss_set_visuals.gd`.

Run the three capture scenes for Tempo layout, boss sets and set descriptions. The integration capture uses `-- --class=ranger --level=60 --map=sanctuary --slot=96 --starter=0 --touch=0`. Generate the PDF with `tools/create_cheats_pdf.py`.

## Remaining limits and recovery

Fresh critic creation failed at the agent-thread limit; existing builders could not count as blind reviewers. Later builder usage limits were reached; root completed the remaining validation and exports. No independent quality approval is implied.

Observed build/review passes: Tempo 2; original armory/crossbow poses 4; boss art 3; catalog mechanics 2; integration harness 3. These include internal fixes, not blind-comparison decisions. Context usage telemetry was unavailable. No eight-pass limit was exhausted and no valid blind-review rejection was received.

The baseline commit remains recoverable. Build binaries are in ignored `build/`; source, assets, PDF and this evidence are committed. Pre-existing depth output files and the user's running editor were preserved. Smallest next verification work: a physical Android playtest and fresh independent comparison of the final rendered evidence.
