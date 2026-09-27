# bh-009 handoff — Mobile "total efficiency" mode, epic title intro, touch Roll button

Status: **IMPLEMENTED — real low-end phone UNVERIFIED** (no device here; verified on this PC's renderers and the Android
emulator). Nothing committed (user rule: work on `main`, uncommitted). Working tree on `main` over 19d1de8 + bh-008.

## What the user gets
| Area | Change | Main files |
|---|---|---|
| **Efficiency mode** | Choosing **Mobile** turns it on (phones always default on; PC turns it off; toggle in Settings > Video > Performance). Preset: no shadows, no post effects/AA, 3D at 70 %, 30 fps cap, coarser LODs, max 3 catch-up physics steps. Saves no longer override device settings (a desktop save used to bring back shadows and an uncapped frame rate on a phone). | `autoload/settings.gd`, `settings_window.gd`, `platform_prompt.gd`, `main.gd` (`--lite=`) |
| **Phone renderer** | Android/iOS now use the OpenGL **Compatibility** renderer (fastest on budget GPUs, avoids buggy Vulkan drivers); max 8 renderable lights on mobile. APK now also ships **32-bit ARM** (armeabi-v7a) for cheap phones. | `project.godot`, `export_presets.cfg` (local) |
| **Lighter maps** | Decoration cut into 24 m cells (culled; also on PC, lossless) and undergrowth thinned (ferns 20 %, grass 35 % …); terrain drawn as 24 m tiles at 2 m with a 5-read shader (was 16 reads); cheap unlit water; no mist, light shafts, sky, SSAO, glow, colour grade; ambient/exposure lifted to keep PC brightness. **Collision, navmesh, spawns, teleporters identical** (tested). | `map_builder.gd`, `material_library.gd`, `world_shaders.gd`, `maps/westreach.gd` |
| **Runtime governor** | `Perf` autoload: only the 6 lights nearest the hero shine (renderer-side; node visibility untouched); off-screen / far characters stop animating. Debug builds on a phone log `BH_FPS` every 5 s (`adb logcat -s godot`). | `autoload/perf.gd` |
| **CPU** | Blend spaces without `sync` in lite (was ~90 % of animation cost); far, calm enemies doze and wake before their sight range; minimap re-renders only on movement, markers at 10 Hz; 40 % particles; no flash lights; camera far plane 90 m. | `character_visual.gd`, `enemy.gd`, `minimap.gd`, `vfx_lib.gd`, `gore.gd`, `loot_fx.gd`, `town_portal.gd`, `player_camera.gd` |
| **Title intro** | Plays once per launch before the title screen: aether charge → BEYOND letters slam in → HEROES crashes in (flash, double shockwave, lightning, spark storm, shake, god rays) → ornament draws out → gold sheen → "by Aljay Leodones" blade-slash reveal → wordmark and byline glide into the live menu. Any key/click/tap/Back skips. Pure 2D. `--title_intro=0` skips (tools). | `ui/menu/title_intro.gd`, `main_menu.gd`, `main.gd` |
| **Touch Roll button** (user follow-up) | New **Roll** button next to Dodge: always a forward roll (along the stick, or the way the hero faces). Dodge keeps roll-with-stick / backstep-without. | `ui/mobile/touch_controls.gd`, `touch_button.gd`, `player.gd` |
| Test fix | `test_loot` assumed auto-loot off; the player's own settings had it on. Now pinned in the test. | `tests/unit/test_loot.gd` |

## Evidence (`evidence/`)
- Perf, old phone path (Mobile/Vulkan, desktop quality) → efficiency mode on Compatibility, this PC 1600x900 vsync off
  (`perf/summary.md`, `perf/*.json`):

| Map | Triangles/frame | Active lights | GPU ms | Frame ms avg / p95 | VRAM MB |
|---|---|---|---|---|---|
| sanctuary | 1.62 M → 151 k (÷11) | 67 → 6 | 4.78 → 1.03 | 5.4 / 8.1 → 2.9 / 4.7 | 452 → 220 |
| westreach | 1.31 M → 68 k (÷19) | 70 → 5 | 2.68 → 0.99 | 8.7 / 17.0 → 2.6 / 3.6 | 474 → 228 |
| olivar | 0.71 M → 96 k (÷7) | 66 → 6 | 2.77 → 0.98 | 3.7 / 5.9 → 2.4 / 3.0 | 406 → 225 |
| wyman_outpost | 1.09 M → 76 k (÷14) | 45 → 6 | 3.06 → 1.05 | 4.8 / 7.0 → 2.7 / 4.1 | 459 → 231 |
| ruined_forest | 1.88 M → 85 k (÷22) | 27 → 5 | 6.68 → 1.15 | 24.7 / 40.5 → 4.8 / 9.0 | 470 → 235 |
| catacombs | 1.76 M → 166 k (÷11) | 69 → 6 | 3.66 → 0.95 | 12.0 / 20.7 → 3.8 / 6.5 | 414 → 191 |

- Map build (headless, this CPU) `baseline_load.json` → `lite_load.json`: Westreach 2.06 → 1.46 s, Ruined Forest 0.78 → 0.52 s,
  Olivar 0.57 → 0.42 s, Wyman 0.56 → 0.39 s; navmesh polygon counts identical.
- Captures: `compare/pc_vs_mobile.png` (6 maps), `intro/title_intro.gif` + `intro/contact_sheet.png`, `roll/controls_with_roll.png`,
  `android/` (emulator: intro, title screen, in-game in efficiency mode, steady `BH_FPS 30` after continuing a save).
- Tests: `tests_final.txt` — **10,950 checks, 0 failures** (new `test_perf`, 7 tests). compile_all: 0 failed.
- APK: `build/BeyondHeroes.apk` (debug, arm64 + armv7, 213 MB; a release export is much smaller).

## Known / not done
- Real low-end phone not tested (emulator on host GPU only). The emulator's software GPU (SwiftShader) cannot link Godot's
  own 2D canvas shader (uniform limit 261); host-GPU emulation and desktop OpenGL are fine. If a real phone shows a blank
  screen, `adb logcat -s godot` will show it.
- Tool-driven screenshots (`perf_probe`, `check_roll`) catch the loading card: `get_image()` on the Compatibility renderer
  returns a stale frame there. Movie-writer captures (`--write-movie`) are correct.
- PC mode is unchanged except the lossless decoration chunking and the save/device-settings fix.
