# Beyond Heroes beta QA baseline

Date: 2 October 2026, Asia/Manila. Game revision: `cd7f368e`. Godot 4.7.2. Codex added a QA-only performance entry point; no gameplay optimization has been applied yet.

## Results that affect release

The existing game is not yet a verified beta release. The complete correctness suite has 34 failed assertions. The multiplayer integration probe exits successfully but logs runtime errors. Dense combat misses both PC and mobile frame-time targets on this relatively strong desktop.

Claude Code programming briefs are prepared, but Computer Use cannot capture or target the existing Claude desktop input. The user was asked to paste the brief instruction. No Claude programming work or successful prompt delivery has been confirmed for this request.

## Correctness

- Account service: 23 tests passed, exit 0.
- Godot: 122,903 checks, 34 failed assertions, exit 1.
- Failed suites: combat power band (10), weapon tempering (1), enemy mechanics/balance (8), inventory/attribute assumptions (15).
- Inventory failures expect Strength scaling for bows/crossbows/javelins while the current implementation gives Dexterity scaling. Check the accepted class design before classifying these as regressions. Never weaken assertions just to obtain a green run.
- Enemy failures include explosions, chain lightning, mimic pull and Webbed status. Review fixture restoration, health recomputation, aiming and actual live behavior.
- Multiple map tests report navigation edge merge warnings. Shutdown logs report leaked instances/resources. Use repeated map transitions to distinguish retained caches from persistent growth or teardown-only leaks.

Full assertions: `godot-baseline-report.json`. Raw suite log: `../beta-baseline-godot-tests.log`.

## Multiplayer

The existing integration probe completed its three stages:

1. Twelve real HTTPS/ENet clients join, save, and fill capacity; thirteenth entry is rejected.
2. Services restart; two clients load real maps, recover characters, trade atomically and save on exit.
3. Custom host and client join with separate characters and shared directory listing.

The twelve-client stage's synthetic clients can report PASS despite null-player errors in `Net._send_enemies` at line 1015. Dedicated disconnect handling also emits ENet channel errors. These need meaningful lifecycle coverage and a clean rerun. The headless probe is not a substitute for interactive two-player combat or remote/mobile connectivity.

The active local server was stale at protocol 15 with zero players. Codex used the project's managed stop/start path, which backed up confirmed saves, then verified protocol 16 and game_online=true. This resolves the local version mismatch. It does not move hosting off the user's PC.

Raw per-process logs are preserved in `multiplayer-process-logs/`.

## Rendering and performance

Machine: Ryzen 7 5700X, 32 GB RAM, NVIDIA RTX 4060. Window: 1280x720. Frame caps and VSync disabled for measurement. Mobile profile uses the PC's OpenGL compatibility renderer and existing efficiency/touch flags; it is not a phone measurement.

| Scenario | Median frame | p95 frame | p99 frame |
| --- | ---: | ---: | ---: |
| Town, desktop | 7.46 ms | 12.13 ms | 12.80 ms |
| Town, mobile renderer | 9.73 ms | 15.29 ms | 16.20 ms |
| Forest, desktop | 10.78 ms | 16.88 ms | 20.36 ms |
| Forest, mobile renderer | 12.38 ms | 19.52 ms | 22.67 ms |
| Forest + 40 enemies, desktop | 56.22 ms | 79.82 ms | 110.11 ms |
| Forest + 40 enemies, mobile renderer | 64.17 ms | 80.83 ms | 157.79 ms |

Ordinary scenes sample 900 frames across three spawn locations. Combat samples 300 frames after warm-up; 54 enemies were engaged at the end of the desktop run and 51 in the mobile-renderer run. Scene/gameplay variations and one run per scenario limit comparisons. Repeat fixed scenarios before claiming an optimization improvement.

The mobile town profile cuts lights from 88 to 6, primitives from roughly 2.1 million to 0.8 million on average, and reported graphics memory from 571 MB to 267 MB. Draw calls remain approximately 1,600. Investigate scene batching, shared materials, visibility and actor complexity after attributing their cost.

Desktop dense combat reports median process time around 33 ms and physics around 16 ms, as well as GPU time around 14 ms. Removing physical-bone simulators in a diagnostic run yielded a 47.95 ms median / 58.92 ms p95. Removing enemy-to-enemy collisions in a separate diagnostic yielded 45.87 ms / 58.38 ms. Both still miss the budget. End-of-run engaged counts differ (49 and 50 versus 54); repeat a deterministic matched encounter before claiming a precise improvement. These variants change the test scene only and are not candidate gameplay fixes.

The existing probe's ordinary-scene process monitor statistics exceed observed frame intervals in places. Treat those CPU values as requiring validation of sampling/aggregation. The wall-clock frame percentiles, renderer and actual window are recorded separately. New QA wrapper adds medians and sample counts; it does not modify the shipped game's performance.

Four repeated town/forest/tavern cycles completed successfully. Town rebuilds measured 359-630 ms, forest 1,211-1,743 ms, and warmed tavern 54-55 ms (first 228 ms). Sampled process working set peaked around 898 MB and private memory around 1,306 MB. End-of-run values were approximately 892/1,278 MB. This is a short Windows test that includes cache warm-up; it does not prove a leak or Android memory use. Longer per-map resource/count tracking is needed to verify a stable plateau. Raw memory samples: `map-transition-memory.json`.

Run command: `output/beta-20261002/run-render-baseline.ps1`. JSONs, stdout/stderr and screenshots are in this folder. No low-end PC, physical Android device, thermal endurance or impaired-network result has been verified.

## Hosting

A Singapore Linux VM with public IPv4 and direct UDP support is a practical candidate. Start sizing at 2 GB RAM and 1-2 vCPUs, then verify under representative twelve-player load. DigitalOcean currently lists 2 GB / 1 vCPU at US$12/month and 2 GB / 2 vCPUs at US$18/month: https://www.digitalocean.com/pricing/droplets

Required work includes supervised Python/Godot processes, HTTPS, persistent SQLite, tested restore, rolling logs, reboot startup and update/rollback. The coordinator currently validates an HTTPS loopback address using the same configured certificate; a public hostname certificate requires a deliberate internal connection design. Linux SIGTERM/child shutdown also needs review.

The user has not supplied a cloud destination or approved a specific expense. No VM has been purchased or provisioned. Combat remains client simulated; public competitive integrity is not established by hosting the coordinator elsewhere.

## Builds and release status

Existing Windows/Android tools and Godot export templates are installed. ADB detects no Android device. Windows baseline release export succeeded and a headless EXE startup exited zero. Android release export failed because no release signing identity is configured; previous APKs use debug signing. A separate debug baseline APK exported successfully and verified APK signatures v2/v3. It is version 0.8.0/code 1, minimum SDK 24, target SDK 36, with ARM32/ARM64 libraries.

Artifacts: `build/beta-20261002/BeyondHeroes-baseline.exe` (572,186,016 bytes) and `BeyondHeroes-baseline-debug.apk` (521,007,252 bytes). SHA-256 receipts are in `baseline-builds.json`. These builds retain known baseline failures. A polished release requires Claude's fixes and verified reruns, plus a stable Android release signing identity. The QA/design/hosting foundation is prepared for main; no gameplay polish is claimed. Preserve existing signing identity, player data and unrelated local model/document work.

Progress screenshots are fresh baseline evidence in `baseline-menu-*.png` and `gameplay-screenshots/`. Tiny secondary text at 720p needs a design pass. No screenshot here claims that polishing or low-end certification is complete.

Draft off-PC service/Caddy/client configuration is in `server/deploy/`. Its two-certificate proxy layout preserves verified loopback TLS while providing public certificate trust externally. Linux installation, reverse-proxy rate-limit behavior, backup retention, public connectivity and cloud account/cost selection remain unverified/pending.
