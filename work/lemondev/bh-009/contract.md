# bh-009 contract — Mobile "total efficiency" mode + epic title intro

Run id `bh-009`, 28 September 2026. Engine Godot 4.7.2 (Jolt), Windows 10, RTX 4060. Branch `main`, uncommitted working
tree (user rule). Baseline: HEAD 19d1de8 plus the uncommitted bh-008 work (platform prompt, touch controls, net).

## Request (user, verbatim intent)
- The Mobile version is unplayable: loading and graphics are far too demanding. Low-end phones must be able to play.
  Choosing **Mobile** at the start (PC / Mobile prompt) must put the game in **total efficiency / total optimization**.
- The title screen must first play an **epic, high-octane, effects-rich, punchy animation** of the title "Beyond Heroes"
  (action-RPG style), then "by Aljay Leodones".

## Baseline measurements (before any change; `evidence/perf/base_*.json`, `evidence/baseline_load.json`)
Old phone path = Mobile (Vulkan) renderer, desktop quality. Measured on this PC, 1600x900, vsync off:
- Westreach: ~4.0 M triangles per frame, 70 active lights, GPU 3.5 ms, frame 7.8 ms.
- Attribution (Westreach, ablation): AnimationTrees 5.7 ms of CPU per frame for 20 characters (blend spaces with
  `sync = true` evaluate every clip every frame); decoration MultiMeshes are map-wide (never culled).
- Map build: Malasugue 2.0 s, Westreach 2.1 s + 0.5 s navmesh bake (desktop CPU).

## Components (one owner each)
| # | Component | Files | Acceptance |
|---|---|---|---|
| C1 | Efficiency setting | `settings.gd` (efficiency_mode, Mobile preset), `main.gd` (`--lite`), `settings_window.gd`, `platform_prompt.gd` | Mobile turns it on (no shadows/post/AA, 70 % render scale, 30 fps); PC turns it off; phones always default on; saved; toggle in Settings > Video |
| C2 | Phone renderer | `project.godot` | phones use the OpenGL Compatibility renderer; every shader compiles there |
| C3 | Lite world build | `map_builder.gd`, `material_library.gd`, `world_shaders.gd` | decoration chunked (culled) + undergrowth thinned; tiled 2 m terrain with a 5-read shader; lite water; no mist/shafts/sky/SSAO/glow/grade; no shadows; **identical collision, navmesh, spawns, teleporters** |
| C4 | Runtime governor | `autoload/perf.gd` | light budget (5 nearest), animation sleep off-screen/far; nothing touched when efficiency is off |
| C5 | Actor cost | `character_visual.gd`, `enemy.gd` | blend spaces without sync in lite; far calm enemies doze and wake before sight range |
| C6 | Effects + HUD | `vfx_lib.gd`, `gore.gd`, `loot_fx.gd`, `town_portal.gd`, `player_camera.gd`, `minimap.gd` | 40 % particles, no flash lights, far plane 90 m, minimap re-render on movement only |
| C7 | Title intro | `ui/menu/title_intro.gd`, `main_menu.gd`, `main.gd` | charge → BEYOND letter slams → HEROES crash (flash, shockwaves, lightning, sparks, shake, rays) → ornament → sheen → "by Aljay Leodones" slash → hand-off into the live menu; skippable (key/click/tap/Back); once per launch; pure 2D |
| C8 | Tests + tools | `tests/unit/test_perf.gd`, `tests/tools/perf_probe.gd`, `mesh_census.gd`, `capture_intro` | suite 0 failures; compile_all 0 failed |

## Gates
- Headless suite: 0 failures (new `test_perf`). `compile_all`: 0 failed.
- Perf probe on 6 maps, old phone path vs lite + Compatibility renderer: triangles, lights, GPU ms, frame ms, VRAM.
- Real captures: lite maps (Compatibility renderer), intro frames/GIF, title hand-off.
- Android APK builds with the new renderer.
- Real low-end phone: **UNVERIFIED** unless the user tests on one (no device here; the desktop numbers are proxies).

## Invariants
- Desktop (PC mode) visuals and behaviour unchanged except lossless decoration chunking (same instances, culled per cell).
- No Filipino names. Probes use slots 93–99. Never kill Godot by image name.
