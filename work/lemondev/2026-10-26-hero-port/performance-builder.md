# Performance and display settings builder

Pass: 2 of 8. Builder status: IMPLEMENTED — UNVERIFIED pending execution and independent review.

Owned files: `game/src/autoload/settings.gd`, `game/src/autoload/perf.gd`, `game/src/ui/windows/settings_window.gd`, new `game/src/core/android_refresh.gd`, and new `game/tests/unit/test_refresh_settings.gd`.

The first mobile launch still uses the 30 FPS cap and the existing light rendering preset. Selecting a frame limit now preserves that numeric preference when changing efficiency or controls, including migration of old settings files. The settings UI includes 90, 120, 144, 165 and 240 FPS, preserves custom numeric caps, reports the current display refresh rate, and describes the hardware/OS limits. Restoring Video defaults on a phone retains the safe mobile preset.

On Android, the optional helper uses the built-in AndroidRuntime and JavaClassWrapper to send a Surface frame-rate hint. A numeric cap requests that rate; Unlimited requests the maximum mode reported by the display. Android remains responsible for choosing the actual rate. The helper checks method availability, null objects, surface validity and Java exceptions. Calls happen when a cap changes or the app resumes, with at most one delayed 0.5-second retry for a surface that is not ready. A newer request invalidates an older retry. Unrelated settings changes do not issue additional hints.

The Android API route was inspected against the installed Godot 4.7.2 Android export template, without installing another dependency. `javap` output and template/jar SHA-256 hashes are in `output/hero-port-20261026/android-api/`. The Android SDK 36 Surface APIs were also inspected locally. `AndroidRuntime.getApplicationContext()` and `getActivity()` carry the `UsedByGodot` annotation. No physical Android device is attached, so high refresh behavior, Java wrapper execution, Android lifecycle and device performance are unverified.

The animation governor had a correctness defect: an awake companion could retain a coarse animation stride after efficiency mode was turned off, because only off-screen visuals were restored. Awake visuals no longer eligible for ranking and portraits now return to stride 1. No animation timing or combat logic was changed. Volumetric fog now follows the same efficiency switch as SSAO/glow when settings are applied to an existing map.

No governor performance micro-optimization is claimed. Its sorting/distance work runs at 5 Hz; evidence is needed before treating it as a frame bottleneck. Real rendering measurements belong to the integration owner's matched baseline/candidate runs. The builder has not accepted its own changes and does not claim any achieved rendered FPS.

Planned focused command (coordinate with integration before executing):

```powershell
& 'A:/Installer/Godot_v4.7.2-stable_win64/Godot_v4.7.2-stable_win64_console.exe' --headless --path game res://tests/run_tests.tscn -- --only=test_refresh_settings,test_perf,test_bh014,test_bh037
```

`test_refresh_settings` covers a fresh safe mobile default, explicit high refresh selections, preset/control-mode transitions, old settings migration, custom numeric limits, restoration of full-rate companion poses, and the optional Android path on desktop. The fixture overrides apply/save and writes only `user://refresh-settings-unit.cfg`, which it removes after loading.

Static validation: `git diff --check` passed for owned source files. The integration owner's `output/hero-port-20261026/overlay-and-model-tests.log` reports `test_refresh_settings` 5 tests / 32 checks and `test_overlay_budget` 6 tests / 83 checks, all passing. The combined hero/overlay/settings/touch run reports 2,669 checks and zero failures. These were root-executed tests, not builder engine runs. Independent review and final integrated rendering remain pending. Physical Android: unavailable.

## Pass 2: inactive character overlays

The integration owner ran a matched 40-enemy overlay ablation on the candidate staging copy. Both runs used custom body, touch controls, mobile profile on desktop, 1280×720, a 90+20 frame warmup and 1,200 sampled frames. Reports, raw frames, commands and source hashes are under `output/hero-port-20261026/perf/overlay-ablation/`. The fully disabled-overlay run is diagnostic: it removes visible flashes/rims too and is not the production implementation.

Observed pair: overlay-on median 53.29 ms / p95 72.26 ms, 2,257.5 median draw calls, CPU render 17.58 ms and GPU 13.30 ms. Overlay-off median 51.05 ms / p95 70.97 ms, 1,500 draw calls, CPU render 16.04 ms and GPU 12.18 ms. This shows a redundant draw burden and only a modest wall-time opportunity; it does not establish a production speedup or meet the dense performance targets.

Approved production change: `CharacterVisual` attaches its overlay only while flash intensity, rim intensity or a bounded loading warmup is nonzero. Shader/material resources remain alive. Assignment work happens on state changes rather than every tween update. Newly adopted hair, worn gear, regalia and weapons inherit the current state; release/unequip clears their overlay ownership. The material is retained across body replacement, preserving live flash color/intensity and status rim state. Replacing a flash kills the old bound tween.

`FX.warm_up()` attaches the black pass to registered live visuals for its existing three loading frames, then restores each visual's live flash/rim state. A counter balances overlapping warmups. This preserves the existing opportunity to compile overlay variants during loading without adding a timer or perpetual process callback. Actual first-hit rendering still requires the integration owner's check.

New focused suite: `game/tests/unit/test_overlay_budget.gd` (six tests): idle/flash/rim overlap, interrupted flashes, adoption/release and stale tracked meshes, real worn gear plus weapon equip/unequip, model switching during a live flash/status, bounded warmup and freeing during a bound tween. This builder did not launch Godot. Static diff checks passed. Root owns execution, captures, final performance evidence and acceptance.

The pair runner `tools/overlay_ablation.py` passed Python compilation/help and launches only sequential Godot processes. It rejects the console wrapper, has a 240-second per-process timeout with process-tree termination limited to that spawned PID, checks fresh reports/sample counts/script errors and records source hashes.

Remaining measured gap: dense CPU/physics cost. On the frozen first baseline cycle mobile profile used 2.98 physics steps per rendered frame; median wall time was 59.75 ms while GPU was 14.66 ms. Desktop median wall time was 37.31 ms while GPU was 7.44 ms and CPU render was 3.86 ms. The next proposed diagnostic is the existing `--no_enemy_collide=1` probe flag, holding all other conditions fixed, to bound jammed enemy-capsule collision work. It is an ablation only, not a proposal to remove gameplay collision in the shipped game. No simulation source has been edited.

Public API references inspected: [Godot JavaClassWrapper](https://docs.godotengine.org/en/stable/classes/class_javaclasswrapper.html), [JavaObject method guard](https://docs.godotengine.org/en/stable/classes/class_javaobject.html), [Android frame-rate API](https://developer.android.com/media/optimize/performance/frame-rate). The exact installed API signatures in the local evidence are authoritative for the implementation. These references explain the optional nature of the frame-rate request; they are not device test results.
