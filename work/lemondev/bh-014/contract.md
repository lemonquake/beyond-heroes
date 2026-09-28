# bh-014 contract — performance pass ("run smooth at all times, like Torchlight")

Run id `bh-014`, 29 September 2026. Godot 4.7.2 (Jolt), Windows 10, RTX 4060, Ryzen 7 5700X. Branch `main`, baseline
HEAD 653268f. Benchmark reference: the user named Torchlight / Torchlight 2 (no footage supplied); the gate is therefore
numerical (frame times, hitches), not a visual comparison.

## Request (user, verbatim intent)
- Very poor FPS in Westreach, Ruined Forest and other big maps. Optimize for real (not "very low settings"), the way
  commercial ARPGs such as Torchlight 1/2 stay smooth at all times. Push everything to `main` and update the APK.

## Baseline (before any change; `evidence/perf/base_*.json`, `base_ablate_*.txt`)
Desktop quality (Forward+, shadows High, SSAO, MSAA 2x), 1920x1080, vsync off, perf_probe (8 spawn spots x 120 frames):
- Westreach: frame 113.2 ms avg / 133.4 p95 (~9 fps), GPU 29.5 ms, 137 active lights.
- Ruined Forest: frame 80.2 ms avg / 122.1 p95 (~12 fps), GPU 16.9 ms.
- Attribution (ablation): Westreach — monster `_physics_process` ~100 ms of 108; Ruined Forest — AnimationTrees ~25 ms
  (blend-space sync + off-screen characters), monsters ~11 ms.

## Components
| # | Component | Files | Acceptance |
|---|---|---|---|
| C1 | Monster simulation LOD | `enemy.gd`, `actor.gd` | far calm monsters doze on every platform (any hero incl. multiplayer keeps them awake); throttled path requests; neighbour-grid separation at 20 Hz; resting bodies skip the sweep |
| C2 | Spawn cost | `character_visual.gd` | a monster spawns in < 60 ms (was ~900 ms) |
| C3 | Animation LOD | `perf.gd`, `character_visual.gd` | off-screen/far characters stop animating on every platform (never a portrait); monsters (not bosses/heroes) skip zero-weight clips |
| C4 | HUD | `minimap.gd`, `item_slot.gd` | minimap renders on leaving an over-sized render (not 5x/s), no lights or sun shadows in its view; idle slots don't process |
| C5 | Hitches | `fx.gd`, `game.gd`, `audio_manager.gd`, `flicker_light.gd` | first blow of a session < 40 ms worst frame (was ~350 ms); SFX prefetched; shadowed fires never move |
| C6 | Tools + tests | `perf_probe.gd` (`--stress`, `--firsthit`, `--load_bench`, `--ablate_process`, `--spawn_bench`), `tests/unit/test_bh014.gd` | suite: no new failures vs the bh-013 baseline (19 known) |

## Gates
- Exploring (perf_probe) Westreach + Ruined Forest: avg < 16.7 ms and p95 < 16.7 ms (60 fps with headroom) at desktop
  quality, 1080p.
- 40-monster brawl (`--stress=40`): report avg / p95 / p99 / max; no frame over 400 ms caused by spawns.
- First hit: worst frame < 40 ms with the warm-up (3 runs each, cold vs warm).
- Visual invariants: nothing a player can see changes (sleep only beyond sight, animation sleep only off screen, minimap
  identical content), collisions and combat rules untouched.
- Android APK rebuilt.

## Invariants
- No quality settings lowered. No Filipino names. Probes use slots 93–99. Never kill Godot by image name (the user's
  editor, PID 6520, stayed open all run).
