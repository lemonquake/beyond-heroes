# Beta readiness: current QA evidence

Codex audit started 2 October 2026. Baseline revision: `cd7f368e` (verified with `git rev-parse --short HEAD`; no new release commit yet).

## Completed

- Read project/server architecture and existing multiplayer/profiling tools.
- Wrote `docs/BETA_RELEASE_PLAN.md` and `docs/CLAUDE_BETA_MASTER_PROMPTS.md`.
- Ran `python -m unittest server.test_service`: 23 tests, exit 0.
- Rendered fresh server-choice, account and server-settings screenshots using the existing `capture_server_menu.tscn` tool. Screenshot canvas is 1920x1080 even with a 1280x720 window override.
- Ran the existing real HTTPS/ENet integration probe: exit 0. Twelve-client/capacity/saving, two-client restart/trade and custom host/join stages passed their assertions. Runtime errors remain in raw logs, so this is not a clean multiplayer QA pass.
- Checked `adb devices`: no Android device attached. Real-device install, touch, thermal and performance checks remain pending.
- Full Godot suite finished: 122,903 checks, 34 failed assertions, exit 1. Failed suites: `test_balance` (10), `test_bh017` (1), `test_enemies2` (8), `test_inventory_overhaul` (15). Full report copied to `godot-baseline-report.json`. Inspect failures against current intentional class mechanics before changing behavior or test expectations.
- Restarted the zero-player local official server with the project's managed controls after confirming protocol 15 was stale. Stop saved a backup. Verified the restarted service reports protocol 16, zero players and game_online=true. This fixes the local version mismatch; it is still hosted on the user's PC.

## Additional completed work

- All six baseline render scenarios finished, plus two diagnostic variants and twelve map transitions. Dense combat median frame time: desktop 56.22 ms, mobile renderer 64.17 ms. See `QA_BASELINE_REPORT.md` for all percentiles, caveats and memory/load observations.
- Windows baseline EXE exported successfully and passed headless startup (exit 0). Android release export failed because release signing is not configured. A separate debug APK exported with the existing identity and passed signature verification, with ARM32/ARM64 libraries. No Android device is attached for launch/performance checks.
- Draft Linux service/Caddy/client configuration is in `server/deploy/`, with public UDP connectivity, lifecycle, rate-limit and backup verification still required.
- QA/design/hosting foundation has been committed and pushed to main. Baseline builds and screenshots remain available locally. Only task files were committed; the pre-existing cheats-document edit and female model files were preserved.

## Pending

- Claude UI: screenshots time out; accessibility exposes only an empty window shell; targeting a returned button failed with `coordinate input geometry is unavailable`. User was given the one-sentence brief instruction to paste into Claude Code. Delivery has not been confirmed yet.
- Gameplay polish/optimization, fixing or classifying the 34 baseline failures, and a clean multiplayer lifecycle rerun.
- Cloud account/host selection and approved cost, Linux hosting verification, public connectivity and player-data migration if needed.
- Physical low-end PC/Android testing and a stable Android release signing identity.

## Findings for Claude to address

1. Integration exit status alone misses runtime script errors. Fresh client logs show `Invalid access to property or key 'global_position' on a base object of type 'Nil'` from `_send_enemies` at `game/src/net/net.gd:1015`, followed by `OFFICIAL_PROBE PASS`. The avatar fallback unconditionally dereferences `Game.player`. Diagnose the no-player/teardown state and add meaningful coverage. Do not just suppress logs.
2. Dedicated-server logs contain disconnect-time ENet errors: `Unable to send packet on channel 0, max channels: 0`, with backtraces in `_chat_system` and `_rpc_peers`. Determine whether recipient filtering or lifecycle ordering is needed; verify ordinary departures and shutdown.
3. The current configured local server reports an incompatible version in a freshly rendered menu, while the source Python service and game both declare protocol 16. Inspect the running service version without restarting live services prematurely. Public packaging needs matching client/server versions and understandable status.
4. Fresh server UI shows `Enter the Realm`. Use the user's requested plain labels, such as `Play Online` or `Sign In`. Review text size/contrast at the actual window size, including secondary text.
5. Standard public-host players should have a bundled hostname and public certificate trust. Move certificate-file paths and setup-only private-key guidance into an advanced section/manual when practical; preserve the trusted self-signed custom-server path.
6. Existing `bench_bh031.gd` documents `--lite=1` but does not apply it in the script. Validate benchmark settings rather than assuming a command flag takes effect. `perf_probe.gd` creates Main and does process those flags; use verified runtime fields in reports.
7. Offline developer tools and cheat systems are intentional existing content. Preserve them; audit official-mode restrictions and public export test-scene exclusions without deleting intended offline features.
8. Public TLS hosting needs an internal-connection design: `Net._server_request` connects to `https://127.0.0.1` and loads the same configured certificate as its trust chain. A normal public-domain certificate will not include loopback in its SAN. Keep internal requests authenticated and local, and validate the configured server name correctly; do not disable TLS verification as a workaround.
9. Account service catches KeyboardInterrupt but has no explicit SIGTERM handler. On a supervised Linux stop, ensure final backup/cleanup runs and in-flight writes are handled. The parent runner currently terminates children and may skip later cleanup if waiting for a child throws; review bounded graceful shutdown.
10. Baseline `test_balance.gd` finished with 10 failures out of 16 checks. Its live-combat harness reports nearly zero level-one Shadowblade damage, and classes outside its 20% band at later levels. Inspect whether positioning/aim, current class mechanics or stale harness assumptions cause this before changing game balance or loosening assertions. The separate progression/balance audit passes; they exercise different behavior.
11. Fresh 720p PC/mobile-control gameplay captures show very small quest, minimap and status text. Validate readable physical text size in each supported window/device size, with the actual mobile defaults, before treating layout as complete. Mobile screenshots here are PC emulation of touch mode, not phone captures.
12. The first town samples retain approximately 1,600 draw calls in efficiency mode despite reducing active lights from 88 to 6 and reported graphics memory from 571 MB to 267 MB. Investigate static-geometry batching, shared materials, visibility and actor draw cost using attribution, then repeat identical measured scenarios. Do not treat the stronger PC as proof of low-end phone compatibility.
13. The existing performance probe's process-time monitor summaries can exceed observed wall-clock frame intervals, suggesting stale/aggregated monitor values around scene load. Use wall-clock frame-time percentiles as the baseline and validate CPU monitor sampling/refresh before attributing specific script costs. Render and test shutdowns also emit leak warnings; distinguish test teardown from persistent runtime growth with repeated map visits.

## Performance machine

Local render device: NVIDIA GeForce RTX 4060. CPU: AMD Ryzen 7 5700X, 8 cores / 16 threads. System RAM: approximately 32 GB. This machine cannot establish low-end mobile/PC compatibility. Current rendering captures use Godot 4.7.2 Forward+; mobile-renderer measurements remain pending.

## Screenshot paths

- `A:\Python\beyond-heroes\output\beta-20261002\baseline-menu-servers.png`
- `A:\Python\beyond-heroes\output\beta-20261002\baseline-menu-account.png`
- `A:\Python\beyond-heroes\output\beta-20261002\baseline-menu-settings.png`

These are current baseline captures, not polished results. Real-device performance, public hosting, polished release EXE/APK builds and pushing changes are still pending. `build-baseline.py` prepares distinct QA builds and redacts signing arguments from logs; building the baseline does not close the reported failures.
