# BH-021 completion

Recovered Claude Code's unfinished `Game storyline and quest overhaul` session and completed its integration on 29 September 2026. Source and generated assets are committed; Blender character, weapon, texture and music scripts remain reproducible in `tools/`.

Implemented the requested combat and rank progression update alongside the story. Read `docs/COMBAT_AND_STORY_UPDATE.md` for formulas, measured builds, migration behavior, research sources and limitations. Lore section 10 now contains the chapter's canon. The story contract's last step is the conversation about the Black Spire, not a playable rescue chapter.

Validation: 24,396 checks passed in the final 14-suite focused run; all 134 checks passed in the additional progression suite, including percentage-proc scaling. A rendered game run passed the character/rank screen, Paul David placement, surviving Kethrax hit, victory flag and cutscene, and restored controls. Selected screenshots and the JSON report are in `evidence/progression/`. Initial story cutscene contact sheets are retained beside the prior scene captures.

The wider regression run identified eight remaining `test_enemies2` assertions (War Totem reference stats and timed enemy behavior). The older starter-gear class-balance gate remains failing. Neither is represented as passing. Navigation/viewport/shutdown warnings are also described in the update notes.

Godot 4.7.2 Windows release and Android debug-signed exports succeeded. The exported Windows game started headlessly with a level-30 scratch hero and exited successfully. APK verification succeeded. APK contains ARMv7 and ARM64 builds; no physical phone test or production signing is claimed. Release files are local under `build/`, with SHA-256 hashes in `build/build-checksums.json`.

Test and render helpers use scratch save slots 96, 97 or 99. Real save slots were not opened or rewritten. On normal load, old ranks are reassessed once, removed promotion fees are refunded, and existing equipment stays equipped. Multiplayer protocol is 8.
