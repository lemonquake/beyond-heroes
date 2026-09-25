# Systems engineering and validation

## Decoupled data-oriented design

Keep entity/component data separate from rendering, audio, DOM, and UI. Systems receive state/components, configuration, inputs, and delta time; they produce the next state or mutate only their explicitly owned data. Emit events or snapshots for presentation. Avoid hidden global singletons and inter-system side effects. Namespaced IDs, resource ownership, reset, unregister, and dispose paths are part of the interface.

Use the existing engine's ECS or equivalent data-oriented structure; do not introduce a framework merely to satisfy the label. Prefer small modules with no new third-party runtime dependencies. The guide's WebGL2/Three.js/Canvas examples describe a browser pipeline, not a requirement to replace another engine.

Define units, coordinate axes, state invariants, fixed-step policy, seed control, and determinism expectations. Reject invalid/non-finite delta time and state. Use a fixed 1/60-second simulation step for the standard gate; handle elapsed-time spikes with bounded substeps or an explicitly documented clamp. Do not silently discard time and claim frame-rate independence.

The guide's code is illustrative, not production-certified: preserve legitimate zero-valued configuration with null-aware defaults; validate every relevant position/velocity component with finite checks; test lifecycle and boundary behavior. Do not copy its `config.value || default` or single-axis NaN check as a complete solution.

## Required simulation gate

Run **10,000 fixed steps at 60 Hz** for each applicable simulation component. This is about 166.7 simulated seconds, not proof of wall-clock rendering speed. Use deterministic seeds and record the exact tested artifact. Assert finite position/velocity/rotation, physical or gameplay bounds defined in the contract, valid state transitions, and bounded allocation/resource growth. Preserve failing seeds and minimal reproduction data.

Include scenarios appropriate to the change: zero/maximum input, spawn/despawn churn, restart/reset, boundary positions, large delta time, collisions, and long-running accumulation. Use an independent oracle or invariant where possible; a test that repeats the same formula as the implementation proves little.

## Guide stress benchmarks

Apply rows to the relevant subsystems. These are the manual's defaults; record hardware and measurement method rather than claiming they are universal across devices.

| Subsystem | Workload | Required result | Reject for |
| --- | --- | --- | --- |
| Spatial index / octree | 10,000 moving dynamic colliders | Query time below 1.5 ms per frame | Sustained memory growth above 0.1 MB/s, incorrect queries, or missed budget |
| Projectile ballistics | 500 simultaneous raycasted rounds | Zero missed fast-moving hits in the defined test set | Tunneling through 1-unit walls |
| Camera controller | High-speed target rotational snaps | Smooth damping with no measured/visible jitter under a defined tolerance | Gimbal lock, geometry clipping, unstable convergence |
| AI state machine | 100 concurrent agent decisions | Total tick evaluation below 0.8 ms | Invalid transitions, lockups, or missed budget |

Specify percentile, sample window, warmup, units (including MB definition), and jitter tolerance in advance. A useful local convention is p95 for subsystem timings, alongside maximum and failure counts; this is an operational addition, not a percentile specified by the PDF. Measure sustained memory growth after warmup across repeated lifecycle cycles, accounting for garbage collection. Do not infer leak freedom from one heap snapshot.

Verify collision tests with known intersecting trajectories and expected hit IDs, including thin walls and high speeds. For spatial queries compare representative results to a brute-force oracle. Validate AI transition rules and progress/timeout invariants. Camera evidence includes rendered obstruction tests and traces, not just finite numbers.

## Runtime performance and evidence

Measure the assembled game with a real headless WebGL/engine rendering context, recording the backend. For a 60 FPS target the nominal frame budget is 16.67 ms. Define a sustained observation window and acceptable frame-time distribution before the run; a practical default is a 60-second representative window with p95 at or below 16.67 ms, with p99, maximum, and dropped-frame counts reported too. Do not equate this convention with a guarantee that every frame meets budget.

Software-renderer measurements must be labeled; they do not predict target GPU performance. A throttled browser, uncapped simulation loop, or absent WebGL context cannot certify rendered FPS. Run target-device checks when required; otherwise report the performance gate as unverified for that target.

Keep commands, exit codes, raw measurements, timestamps, and revision IDs. A harness crash is a failed/incomplete run. Do not replace actual results with expected values. Pass only the context-safe raw evidence to the Blind Critic as described in `roles-and-review.md`.
