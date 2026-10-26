# Dense combat CPU audit

The unresolved gap is wall-clock CPU cost in dense combat. No actor/enemy simulation source has been changed by the performance builder. Reducing enemy collision masks or collision frequency is not an acceptable shipped optimization for this task.

The existing probe flags separate two questions: `--no_enemy_collide=1` bounds enemy capsule collision work, while `--enemy_cost=1` measures the existing enemy script callback cost without engine collision/render time in that measurement. The latter calls callbacks manually for 120 samples and changes diagnostic state; it does not report rendered FPS. The existing `--freeze=physics`, `--freeze=nav`, `--freeze=visual`, `--no_anim`, `--anim_cost` and `--ablate_process` tools are available, but broad cumulative ablations drift during a live fight and should not rank small changes.

Run the prepared sequence only after the integration owner's other rendering work has finished:

```powershell
python tools/dense_cpu_audit.py --godot A:/Installer/Godot_v4.7.2-stable_win64/Godot_v4.7.2-stable_win64.exe --game A:/Python/beyond-heroes/output/hero-port-20261026/candidate-game --profile mobile
```

Use the final staging path with `--game` if it differs. Optional separate desktop run: change `--profile mobile` to `--profile pc-low`. The script launches three processes sequentially (control, collision-off, callback cost), records exact commands/source hashes, enforces the 240-second process timeout, checks fresh reports and script errors, and saves the enemy/engaged count plus physics-steps-per-frame output. Both rendered variants use 40 enemies, custom body, touch input, 1280×720, 90+20 warmup frames and 1,200 samples. `--no_enemy_collide=1` is the only change in the second variant. Source must remain fixed throughout the sequence. Live-fight outcomes may differ; inspect counts rather than treating matching settings as proof of identical trajectories.

The underlying exact command for the rendered control is:

```text
Godot_v4.7.2-stable_win64.exe --path <staging-game> --rendering-method gl_compatibility --resolution 1280x720 res://tests/tools/hero_port_perf.tscn -- --class=knight --slot=97 --profile=mobile --map=ruined_forest --stress=40 --frames=1200 --body=custom --touch=1 --overlay_settle=20 --out=<fresh-report.json>
```

The collision variant adds `--no_enemy_collide=1`. The callback-cost variant adds `--enemy_cost=1` and writes its measurement to the log rather than the render report.

Code inspection found equivalent-work opportunities, with no measured speedup claimed:

- `Actor.physics_move` recomputes the knock velocity magnitude several times (including the common zero-knock path). A local cached magnitude could be refreshed only after knock velocity changes. This must not cross `move_and_slide`, impact callbacks or `_end_knockback`, all of which can change state. Timers, floor state, knockback travel charging, root control and the existing rest schedule must execute in their current order.
- `Enemy._steer` reads its own global position repeatedly within a straight-line function; a local position snapshot can replace those repeated engine getters because the function does not move the body. Do not retain it across `_face`, `physics_move` or a later step. The aggression exponent appears static in a spawn's difficulty dictionary, but caching it requires proving every mutation path, so it is not proposed without measured script attribution.
- `Enemy._separation` computes a square root for every nearby grid entry before rejecting out-of-range entries. A narrow candidate could reject using squared distance and compute `sqrt` only for contributing neighbors, retaining the same grid, neighbor order, radius and accumulation formula. This is the most concrete bounded equivalent-work candidate if callback cost is material. It cannot remove engine capsule collision work.

Before accepting any future simulation micro-optimization, run 10,000 fixed steps with deterministic seeded inputs against a preserved reference implementation. For separation, compare the returned vector against the reference over randomized neighbor positions/radii, including zero offset and distances at `0.001` and the radius boundary, with explicit finite-vector and epsilon checks. Preserve accumulation order and identical eligible neighbor IDs. For movement, compare position/velocity, floor flags, knockback remaining distance/time, impact order/damage and state changes in wall/body/ledge, root/unroot, launch/landing, standing and crowded cases. Maintain exact callback counts and the existing collision mask, max-slides, rest-check and crowd-LOD schedules. A microbenchmark must show a meaningful callback reduction, followed by a matched rendered recheck; small mathematical savings alone do not justify a gameplay change.

Prepared tools passed Python compilation/help only. The performance builder has not run this audit and has not accepted an actor/enemy change.
