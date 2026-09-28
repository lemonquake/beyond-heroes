# bh-014 handoff — performance pass ("smooth at all times")

Status: **IMPLEMENTED — measured on this PC (RTX 4060, Ryzen 7 5700X), desktop quality, 1080p, vsync off.** No quality
setting was lowered. Benchmark: the user named Torchlight 1/2; no footage was supplied, so the gates are numerical.
The real-phone APK is rebuilt but not tested on a device (no phone here).

## What was wrong (measured, not guessed — `evidence/perf/base_ablate_*.txt`)
| Cause | Cost | Fix |
|---|---|---|
| Godot 4.7 prints a warning **with a full script backtrace** for every `add_blend_point()` without a name; each character built 21 | **~900 ms per monster spawn**; map loads 38–51 s; every summon froze the game ~1 s | name the points (`character_visual.gd`) |
| `NavigationAgent3D.target_position` was assigned every physics step; the engine re-runs A* on every assignment (no equality check) | ~100 ms/frame in Westreach (44 monsters) | re-path on a new errand, or every 0.3 s when the goal drifts > 0.6 m (`enemy.gd`, `tempo.gd`) |
| Separation looped over every monster for every monster (O(n²)) each step | several ms, grows quadratically | shared neighbour grid rebuilt once per step, refreshed at 20 Hz per monster (staggered) |
| Far monsters simulated at full rate on desktop (sleep existed only in Mobile mode) | all camps on the map ticking | Diablo-style active zone on every platform; any hero (incl. multiplayer `net_hero`) keeps monsters awake |
| Off-screen characters animated on desktop; every monster kept all blend-space clips in sync | ~25 ms in Ruined Forest | animation sleep off screen on every platform; monsters (not bosses/heroes/NPCs) skip zero-weight clips |
| Minimap re-rendered the whole map 5x/s, with every light and the sun's shadow pass | ~6 ms in a brawl | over-sized render slid under the disc, re-rendered only near its edge; lights live on render layer 20 which the minimap camera doesn't draw |
| First blow of a session compiled shaders/pipelines, built 48 labels, painted splat textures | **~350 ms freeze** | `FX.warm_up()` behind the loading screen, keeping the materials alive so shaders stay compiled |
| 267 inventory slots processed every frame; shadowed torches moved every frame (shadow map redraw) | small | only shimmering slots process; shadowed fires flicker without moving; SFX prefetched on a thread |
| Jammed packs sweeping 6 slide iterations; resting monsters sweeping every step | ~3 ms in a brawl | `max_slides = 3` for monsters; resting bodies re-sweep every 6th step |

## Results (`evidence/perf/`)
| Scenario | Before | After |
|---|---|---|
| Westreach, exploring (8 spots) | 113.2 ms avg / 133.4 p95 (~9 fps) | **5.1 / 6.9 ms (~196 fps)** |
| Ruined Forest, exploring | 80.2 / 122.1 ms (~12 fps) | **5.8 / 8.7 ms (~170 fps)** |
| Sanctuary / Olivar / Wyman / Catacombs | — | 5.8 / 5.8 / 6.9 / 6.0 ms avg, p99 ≤ 12.3 ms |
| Brawl, +40 monsters (45–54 engaged), Westreach | (54 ms, 1–4 s spawn freezes, after step 1) | **18.4–19.2 ms avg, p99 35–46, max 58–98** (3 runs) |
| Brawl, Ruined Forest | 54 ms avg, max 993 ms (after step 1) | **29–31 ms avg, p99 55–60, max 87–113** (3 runs) |
| First hit of a session (worst frame) | 330 / 345 / 388 ms | **24 / 26 / 26 ms**; first `receive_hit` 15.8 → 1.4 ms |
| Map load (Westreach / Ruined Forest / Catacombs) | 44.7 / 51.2 / 37.8 s | **2.8 / 1.3 / 0.3 s** |
| Mobile path (Compatibility, efficiency mode) Westreach / RF | — | 5.0 / 5.0 ms avg |

Notes: part of the final exploring batch overlapped with a second probe that kept running by mistake (stopped by PID);
the brawl numbers above were re-measured alone. The "before" brawl row was taken after the first fixes, so the real
original brawl was worse. Load "before" = same code with only the blend-point names removed.

## Tests (`evidence/tests_final.txt`)
18,985 checks, 20 failures. 19 are the known bh-013 failures (test_balance x10, test_enemies x1, test_enemies2 x8).
The 20th is test_balance's L20 Knight at −23 % of a ±20 % band: a re-run with the current code passes it (2470.7), a
re-run with the old animation behaviour restored fails it (2215.3) — the sim is seeded by instance ids and swings ~10 %
(`evidence/balance_rerun_*.txt`). New suite `test_bh014` (10 tests, 30 checks) passes.

## Tools
`tests/tools/perf_probe.gd`: `--stress=N` (brawl), `--ablate` (also inside a brawl), `--ablate_process` (per-script),
`--census`, `--spikes=<ms>`, `--firsthit=cold|warm`, `--spawn_bench=ids`, `--load_bench=maps`, `--shot=<png>` (F3 overlay).

## Not done / next
- Hit frames still cost ~15 ms vs ~7 ms (new GPUParticles/lights per blow): an effect pool would flatten them.
- A 90-monster brawl in Ruined Forest is still ~30 ms; the remaining cost is per-monster GDScript AI + Jolt character
  sweeps. Next steps would be AI at 30 Hz for monsters off the hero's immediate ring, or moving steering to C++.
