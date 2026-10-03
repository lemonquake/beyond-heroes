# Where a 40-monster brawl spent its frame (bh-035)

perf_probe --stress=40, ruined_forest, pc-low profile, 1280x720, vsync off; median of per-run medians, 3 runs each
unless noted (single runs vary by up to 25 ms; one "no animation" run read 4 ms and its repeats 31 ms).

| Configuration | median frame |
| --- | --- |
| baseline (before any change) | 31.6 ms |
| animation trees off | 31.6 ms |
| monsters hidden (AI still running) | 10.0 ms |
| monster physics frozen | 9.3 ms |
| Jolt motion queries: no enhanced edge removal, 2 recovery iterations (not adopted) | 29.3 ms |
| quarter resolution / minimap off (2 runs) | 32.1 / 29.3 ms |
| spawn fix + crowd simulation LOD | 20.5 ms |
| + animation stride LOD (instrumented build) | 18.0 ms |
| final code, instrumentation removed | 16.9 ms |

Frame phases (baseline, `--phases=1`): two physics steps 17.8 ms (about 8.8 ms each: monster scripts 6.2, of which
move_and_slide 3.1, steering 0.9, target/status upkeep 0.75 per step), process 8.1 ms, draw 6.8 ms. With monsters hidden
the per-step cost was the same but the frame stayed under 16.7 ms, so only 0.63 steps ran per frame: the brawl was a
physics-step spiral, and per-step savings count twice.

Spawn hitch (spawn_bench_before_after.txt): a humanoid monster cost ~7 ms to spawn plus ~75 ms (up to 141 ms) on the
next frame, before the fix; after it, ~5.5 ms plus a 4-9 ms frame. A visual freed right after setup still cost the next
frame (persona_bench), which pointed at a global side effect: rewriting the shared animation library's loop modes.
