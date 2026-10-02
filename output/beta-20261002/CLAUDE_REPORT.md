# Beta readiness: programmer's report (Claude Code)

Date: 3 October 2026. Baseline revision `f7109cfd` (HEAD when work began). Engine: Godot 4.7.2.

**Status of this work: uncommitted.** Everything below is in the working tree on `main`. Nothing has been committed or pushed. Prompt 4 (final full test run, EXE/APK export, push) has **not** been done. `STATUS.md` (Codex's file) was not edited; this report is separate.

## 1. Summary

| Area | Result |
| --- | --- |
| Multiplayer correctness | Two real bugs found and fixed (null crash; empty map after the map owner leaves in official rooms). All integration stages pass with process logs scanned for errors. |
| Server hardening | Bounded and typed every network handler; trusted-proxy handling; SIGTERM and drain; verified backups and restore; health check. 41 Python tests pass (1 skipped on Windows). |
| Linux hosting | Full package written (`server/deploy/`). **Never run on Linux.** No VM, hostname or budget exists. |
| Readability | Text was about 10 px at 720p. Automatic interface enlargement added; touch text floor added; layout regressions caught and fixed. |
| Performance | One real bug found (minimap re-rendering the whole map every frame at Wide zoom) plus a 20 Hz icon redraw. Town frame time at Wide zoom 6.35 to 2.39 ms. Dense combat (40 enemies) **not** fixed. |
| Failing tests | 34 baseline failures classified. 22 fixed (stale tests or harness faults), 12 remain (`test_balance` band gate). |
| Open-beta blocker | Combat and rewards are still client-simulated. Acceptable for a trusted friends beta; blocks an open community or competitive release. |

## 2. Defects found and fixed (ranked by impact)

| # | Finding | Evidence | Fix |
| --- | --- | --- | --- |
| 1 | **Official rooms: empty map after the map owner leaves.** The dedicated coordinator is not on the roster, so it never received checkpoints. The next hero inherited a map with no monsters. | The new `world-handoff` probe failed: "the checkpoint had 54 monsters but the new owner runs none". | `_send_checkpoint` also sends to peer 1 when it is not on the roster (`net.gd`). Probe now passes. |
| 2 | **Minimap redrew the whole map top-down every frame at Wide zoom.** The render radius (54 m) was smaller than the Wide disc (42 / 0.7625 = 55 m), so the "disc about to slide off" test was always true. | `MMDIAG pending-render frames 120/120`. Town draws 1066 to 412 once fixed. | Render radius now covers the widest zoom plus margin; slack never below 2 m (`minimap.gd`). This explains Codex's finding 12 (about 1,600 draw calls). |
| 3 | Minimap icon layers redrawn every frame on PC. | About 3 ms of a 6 ms town frame. | `PC_HZ = 20`. |
| 4 | `Nil` crash in `Net._send_enemies` (probe printed PASS anyway). | Client logs, Codex finding 1. | Skip the peer when there is no avatar and no local hero. |
| 5 | Dedicated-server log spam `max channels: 0`. ENet empties a leaving client's channels before the engine reports the disconnect. | Dedicated log, Codex finding 2. | `_live_peers()` filters to `STATE_CONNECTED`; used by `_rpc_peers` and `_chat_system`. |
| 6 | Unreliable enemy-state packets of about 3.5 KB exceeded the MTU; each engine warning costs about 45 ms on the owner. | `WARNING: Sending 3532 bytes unreliably` in hand-off logs. | `ENEMY_BATCH = 8`. Warning gone from hand-off logs after the change. |
| 7 | Small text at 720p (quest, party, minimap labels about 10 px). | Fresh 1280×720 captures. | `Settings.effective_ui_scale()` (see section 5). |
| 8 | Auto-Loot panel clipped off-screen at the larger scale. | `ui/pc-720p-after/01_town_hud.png` (before the fix). | HUD places it above the orb when there is no room beside it (`hud.gd`). |
| 9 | Title screen said "Development build". | Capture. | "Beta 0.8.0 · online version 16" (`project.godot` now has `config/version`). |
| 10 | Server menu: "Enter the Realm"; certificate file shown to everyone. | Codex findings 4 and 5. | "Play Online"; certificate file folded under Advanced; subtitle "Choose How to Play". |
| 11 | Vague version-mismatch and connection errors. | Codex finding 3. | See section 4. |
| 12 | Benchmark `bench_bh031.gd` documents `--lite=1` but never applies it (finding 6). | Source. | Not changed. New `beta_release_perf.gd --profile=` applies profiles explicitly and pins the minimap zoom. |

## 3. Multiplayer and server

### 3.1 What changed

- **`NetGuard`** (`game/src/net/net_guard.gd`, covered by `test_net_guard`, 44 checks):
  - Profiles keep known keys only, with clamped strings and levels (name 18, map 64).
  - Ally snapshots, effects, pings and appearance packs must be finite, correctly typed and size-bounded.
  - Per-sender token buckets: hello, map change, profile, chat, ping, effects, snapshots, hits, appearances.
  - A reported hit must come from a hero within 60 m of the monster and the claimed point, and is clamped to a possible size.
  - Checkpoints are capped at 400 KB.
- **Account service** (`server/service.py`):
  - `client_address()` trusts `X-Forwarded-For` only from a configured proxy and uses the right-most entry. A proxied request is never an internal request.
  - SIGTERM, SIGINT and SIGBREAK handlers; request drain; a backup on stop.
  - Backup retention: newest 16 plus one per UTC day for 30 days.
  - `/health` includes `version`. HEAD, PUT, DELETE and PATCH return JSON 404 instead of HTML.
  - `suspicious_progress:*` audit events (level +10 in a save, gold +20 million, experience going backwards, an impossible experience rate). They are informational and do **not** reject saves, because a false rejection would discard an honest player's progress.
- **Runner** (`server/run_server.py`, rewritten):
  - Bounded stop for each child, then kill.
  - Non-zero exit if either child dies.
  - `--stdio` for journald under systemd.
  - Log pruning.
  - A Linux file lock for managed mode.
  - The coordinator runs from `coordinator.json`, which does not name the TLS private key.
- **Tools:**
  - `server/maintenance.py` (backup, verify, restore into staging, replace live).
  - `server/healthcheck.py`.
  - `server/deploy/restore_drill.py`.
  - `setup_server.py` gains `--public-host`, `--data-dir`, `--rotate`.
- **Existing tools:** `net_probe_world.gd` with scenarios `handoff`, `separate`, `reconnect`, `hostile`, `version`, `bandwidth`. The integration probe scans every process log (script errors, engine errors, Python tracebacks; engine shutdown noise is excluded).

### 3.2 Test evidence

| Check | Result |
| --- | --- |
| `python -m unittest server.test_service server.test_hardening` | 41 tests pass, 1 skipped (Linux SIGTERM, impossible on Windows). Covers the HTTP boundary, trusted proxy, internal routes through a proxy, rate limits per forwarded client, backup pruning, damaged and foreign backups, replace-while-busy, runner failure path and desktop stop. |
| `python -m server.deploy.restore_drill` | PASSED (`probe/restore-drill.log`). |
| `python -m server.integration_probe` | Full run: capacity (12 real clients and a refused 13th), restart and resume with an atomic trade, custom room, hand-off, separate maps, reconnect, hostile input: all passed with logs clean. `--stages=version,bandwidth` also passed. Logs: `probe/run4-logs/`. |
| `test_net_guard`, `test_net`, `test_official_server`, `test_chat`, `test_boss_set_network` | Pass. |

The authority statement is in `docs/OFFICIAL_SERVER.md`, "What the server decides (and what it does not)".

### 3.3 Bandwidth (real maps with monsters, 35 s windows, ruined forest, from run 5)

| Players | Map owner upload | Member upload / download |
| --- | --- | --- |
| 2 | about 0.9 Mbps | not measured |
| 4 | about 2.2 Mbps | about 0.24 / 0.73 Mbps |
| 6 | about 3.5 Mbps | about 0.36 / 0.87 Mbps |

The owner's upload scales roughly linearly with the number of players (about 0.6 Mbps per extra client). That projects to about 7 Mbps at 12 players, which matters for a home or mobile owner. Caveats: the owner/member label is taken at the end of the window, and in the 2-player case both clients printed "map-owner", so the 2-player row is muddled. Raw data: `official-integration/bandwidth-summary.txt` (copy before it is overwritten).

## 4. Linux hosting package (`server/deploy/`)

Contents:
- `install.sh`, `update.sh` (verified backup, schema check, health check, automatic rollback, and `--rollback`).
- `beyond-heroes.service` (hardened), backup service and timer, health service and timer.
- `backup-offsite.sh` (inert until `/etc/beyond-heroes/offsite.env` exists), `journald-beyond-heroes.conf`.
- `Caddyfile.example` (blocks `/internal`, strips `X-Server-Key`, sets one `X-Forwarded-For`, bounded access log).
- `build.env.example`, `official.cfg.example`.
- `server/requirements.lock` (cryptography 47.0.0, cffi 2.0.0, pycparser 3.0; the service itself is standard library only).
- `README.md` with layout, network table, operations, update and rollback, verification checklist and known limits.

Design points:
- Two certificates. Players see Caddy's public certificate. The coordinator and the service use a private loopback certificate (730 days, `setup_server --rotate`). This resolves Codex finding 8 without disabling verification.
- Secrets: the internal key lives only in `server.json` and `coordinator.json` (mode 0600).
- Version compatibility is the protocol number (16), shown in `/health` and on the title screen.

**Not verified.** No WSL, Docker or systemd was available. Only `bash -n` and the Windows-side tests ran. Still to do on a real VM: `systemd-analyze verify`, Caddy validation, a public health check, two clients on different networks over UDP 24680, stop and kill behaviour, reboot, restore drill on the VM, update and rollback, certificate renewal, journal cap, and whether Godot can run with a read-only project directory. The owner must supply: provider, region and budget; a host name; SSH access; the Godot 4.7.2 Linux zip with its SHA-512; and an off-VM backup destination.

### Player-facing errors (all unit-tested in `test_bh032.gd`, not yet run)

- Name not found, connection refused (server off or firewall), certificate mismatch (points at Server Settings > Advanced), timeout.
- After a successful sign-in but a failed game join: UDP 24680 may be blocked; try another network.
- Version mismatch: tells the player whether their game or the server is older (`Official.describe_version_mismatch`, `Net.version_refusal`).

## 5. Readability and UI

- **Automatic scale.** The UI is drawn for 1920×1080. In a smaller window the engine shrinks every pixel with it. `effective_ui_scale()` multiplies the player's Interface Scale by `clamp(1 / native_scale, 1, 1.5)`. At 1280×720 it is 1.5, so a 15 px label stays about 15 px. A "Larger Interface in Small Windows" setting (`ui_auto`) turns it off.
- **Pixel-placed screens** (hero select, hero creator, the title column) keep design scale via `Settings.hold_design_scale()`, because they overflowed the smaller canvas. The realm-choice pages (`ServerMenu`) adapt and use the larger scale.
- **Windows** already shrink to fit (`UIWindow.fit_scale`); verified for inventory, character, settings, multiplayer and pause.
- **Touch play** keeps the 1.25 layout (trying 1.5 made the stick and buttons collide with the HUD). `TouchText` raises reading labels to 22 px (about 11 sp on a 400 dpi phone). Hotkey badges are left alone.
- **Not done:** no phone has been tested. The 1920×864 touch captures are PC emulation. Custom-drawn text (party and Tempo HP numbers) was not enlarged. The first-launch platform prompt and tutorial flow were not reviewed.

Captures (`ui/`): `pc-720p-before` vs `pc-720p-after`, `phone-1920x864-before` vs `phone-1920x864-after`, `menus-*`, `title-pc-720p-after`. Each has `notes.json` with engine, renderer, window, scale and quality. Scripts: `capture_beta_ui.gd`, `capture_beta_menus.gd`.

## 6. Performance (RTX 4060, Ryzen 7 5700X, 1280×720, `tools/perf_matrix.py`, 3 repeats)

Profiles: `pc-low` is Forward+ with shadows, effects, textures and anti-aliasing at Low. `mobile` is the OpenGL renderer with efficiency mode, run **on this PC**; it is not a phone measurement.

Frame times in ms (median, then p95, p99). Full table: `perf/compare-baseline-candidate.md`.

| Scenario | pc-low baseline to candidate | mobile baseline to candidate |
| --- | --- | --- |
| Town, default zoom | 3.26 to 2.56 (p95 5.63 to 5.03) | 4.12 to 4.33 |
| **Town, Wide zoom** | **6.35 to 2.39** (p95 11.6 to 5.2; draws 1066 to 412) | **7.25 to 4.40** (draws 1511 to 402) |
| Forest | 5.33 to 2.57 | 6.19 to 6.32 |
| Interior | 2.84 to 1.94 | 5.03 to 4.70 |
| Dungeon | 4.44 to 3.05 | 5.72 to 5.74 |
| Combat, 12 enemies | 9.98 to 8.64 (p95 16.9 to 15.3) | 12.46 to 12.65 (p95 about 20) |
| Combat, 40 enemies | 43.2 to 35.1 (p95 76.7 to 79.6, p99 101 to 141: **not improved**) | 57.0 to 58.8 |

Notes:
- The mobile profile shows no gain at default zoom because the 20 Hz redraw was already used there.
- The pc-low gains in forest, interior and dungeon at default zoom come from the 20 Hz icon redraw.
- The Wide-zoom row exposes the minimap bug. The baseline was taken from the same code with only `minimap.gd` restored to `HEAD`.
- Unreliable metrics: the `script` and `physics` monitor values, and the older per-script `--ablate_process` ranking (the scene drifts from about 43 to about 13 ms while it runs). Use the wall-clock percentiles.

**Where dense combat goes** (40 stress enemies plus about 68 natural, about 100 active):
- Freezing enemy `_physics_process` cut the frame from about 41 to 15 ms.
- Hiding enemies saved about 9 ms. Freezing the physics server saved about 7 ms.
- Switching off animation trees, health bars or physical bones did not help.
- A section timer (reverted) showed enemy `physics_move` at about 9.6 ms per frame, `_steer` 2.8 ms, and everything else about 0.1 to 0.9 ms each. Resting enemies already skip movement.
- No safe fix without changing enemy behaviour, so none was made.
- First-use hitches of 100 to 200 ms were seen on spawn, particles and status icons.

Not done: repeated map-transition resource retention (Codex's 12-visit data is the only evidence); no low-end PC, no phone, no thermal or background/resume test. Device-matrix steps are in `docs/BETA_TESTING_CHECKLIST.md`.

## 7. The 34 baseline test failures

| Suite | Count | Cause | Action |
| --- | --- | --- | --- |
| `test_inventory_overhaul` | 15 | Stale. Docs (`EQUIPMENT_AND_BOSS_BALANCE_AUDIT.md`), the Guide and `StatCalculator` say bows, crossbows and javelins scale with Dexterity. | Test rewritten to assert that (ranged: Dex raises damage and Strength does not; melee unchanged). |
| `test_bh017` | 1 | Stale formula. Quality, tempering and the local affix add into one multiplier. | Test now includes the local affix. |
| `test_enemies2` | 8 | A wall within 3 m of the plaza start blocked line of sight for chain, tongue and web. The bloater and bombardier tests compared HP across a level-up heal. The war totem (an objective) was held to the fighter band. | `_at()` uses the open direction; hit counting replaces HP comparison; totem exempt from the fighter band. Mechanics themselves work. Suite passes (595 checks). |
| `test_balance` | 10 to 12 | Harness fault: melee dummies at 2.4 m were out of a dagger's 1.9 m reach, so Shadowblade dealt about 0.7 dps. | Distance now follows weapon reach. L1 Shadowblade is 17 dps. **12 band failures remain** (Knight +26% to +75% over the mean; Shadowblade about -60% at levels 10 to 30). Game balance untouched. Run log: `balance-after-harness-fix.log`. |

## 8. Items still open

| Item | Notes |
| --- | --- |
| `test_bh032.gd` | Written, **never run**. |
| Full Godot suite | Not rerun after the changes. Known remaining failures: `test_balance`. |
| Windows EXE and Android APK | Not built. Release signing for Android is missing (Codex status). Presets disagree on version (Android 0.8.0, Windows 1.0.0). `export_presets.cfg` is git-ignored. |
| Public hosting and UDP reachability | Pending an account, host name and budget. |
| Real devices | No phone and no low-end PC. All targets (60 FPS at 720p low, 30 FPS efficiency mode) remain targets. |
| Commit and push | Not done. The user authorised pushing finished work to `main`; coordinate so only one party commits. |
| `STATUS.md` | Not updated by this work. |
| Map-transition retention probe | Not implemented. |
| First-ten-minutes review | Visual only (menus and HUD). |

## 9. Cautions for the commit

1. **Do not commit** tracked log files rewritten by my runs: restore `output/official-integration/*.log`. The test runner also rewrites `work/lemondev/bh-002/evidence/tests/report.json` and `work/lemondev/bh-010/evidence/balance.json`; restore them after any run.
2. **Check screenshots for private data.** `baseline-menu-*.png` and `local-server-online.png` show the server-settings page and may show the owner's VPN endpoint `https://26.192.28.40:8443`. My captures replace it with `game.example.com`.
3. **Pre-existing work is untouched:** `docs/CHEATS.md`, the female model files, the player's `settings.cfg` (modification time unchanged) and the export presets. The live PC server (8443 and 24680) was only read, never restarted.
4. **New files to include:** `net_guard.gd`, `touch_text.gd`, `test_net_guard.gd`, `test_bh032.gd`, `tools/perf_matrix.py`, the `server/` additions, and the capture and probe tools under `game/tests/tools/`.
5. **Server key:** the integration probe copies the real `server/data/server.json` into a temp config. No secret was printed or logged.

## 10. Suggested order to finish

1. Run `test_bh032`, then the full suite; fix anything it exposes.
2. Re-run `python -m server.integration_probe` (all stages) and `python -m unittest server.test_service server.test_hardening`.
3. Review the screenshots for private data, then decide the Knight/Shadowblade band question.
4. Update `STATUS.md`, `docs/BETA_TESTING_CHECKLIST.md` (the signing note needs confirming) and refresh the performance table.
5. Export the EXE and APK with the existing signing identity and record hashes, version, ABI and signature verification.
6. Smoke-test the EXE and verify the exports contain no private server data. The export filter already excludes `tests/*`.
7. Commit and push once, without force.
8. On the VM, follow the verification checklist in `server/deploy/README.md`.

## 11. Where things are

| What | Path |
| --- | --- |
| Hosting package and runbook | `server/deploy/` |
| Network guard | `game/src/net/net_guard.gd`, `game/tests/unit/test_net_guard.gd` |
| Multiplayer probes | `game/tests/tools/net_probe_world.gd`, `server/integration_probe.py` |
| Performance harness | `tools/perf_matrix.py`, `game/tests/tools/beta_release_perf.gd`, `game/tests/tools/perf_probe.gd` |
| Evidence (this folder) | `ui/`, `perf/`, `probe/`, `balance-after-harness-fix.log` |
| Docs updated | `docs/OFFICIAL_SERVER.md`, `docs/BETA_TESTING_CHECKLIST.md`, `server/deploy/README.md` |
