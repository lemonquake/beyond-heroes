# Claude Code programming briefs: Beyond Heroes beta

The user has appointed Codex lead designer/orchestrator and Claude Code primary programmer. Work in the already-open Beyond Heroes project at `A:\Python\beyond-heroes`. Read this brief and execute the stages in order. Build on existing systems rather than expanding content. Produce concrete working changes, tests, screenshots and release evidence.

## Prompt 1: baseline and beta readiness

Inspect the actual checkout and any AGENTS.md instructions. Read `docs/BETA_RELEASE_PLAN.md`, the current official server/multiplayer documentation, the latest handoff and relevant source. Preserve all existing player data and pre-existing work: `docs/CHEATS.md` is already modified and four female model files are untracked. Do not reset, clean or stage unrelated work. Do not reveal secrets from `server/data`, signing configuration or stored credentials. Keep the installed Godot 4.7.2 engine and existing export settings unless a measured issue requires a change.

Create a dated evidence folder for this release and a `STATUS.md` with completed work, commands, results and precise blockers. Run existing tests and record baseline failures before changes. Inspect benchmark and capture tools for save/settings side effects. Use isolated test data and safe test slots; never overwrite a real character.

Codex's current baseline findings are in `output/beta-20261002/STATUS.md`; read them before starting fixes. Codex added `game/tests/tools/beta_release_perf.gd` and its scene solely for QA: it holds resolution at 720p and extends the existing performance summaries. Coordinate before editing that harness or starting simultaneous performance runs.

Review the player's first ten minutes, desktop and mobile menus, readability, controls, feedback and multiplayer setup. Produce a ranked defect list based on actual source/runtime evidence, then implement the high-impact fixes in coherent small changes. Preserve lore, balance, content, save IDs and offline/custom/official separation. Avoid speculative rewrites and additional game systems. Use plain labels such as Play, Settings, Shop, Team, Pause, Resume and Match Results. No slogans, tiny uppercase informational text, military language or invented technical labels in player interfaces.

Capture screenshots as you work. Save fresh PNGs for desktop and mobile menus, gameplay, settings, multiplayer and each visible fix. Include before/after evidence when applicable, using real rendered game captures. Write absolute screenshot paths and what they prove in STATUS.md. Do not claim old screenshots are new progress.

## Prompt 2: multiplayer and off-PC server

Audit `server/`, `game/src/net/net.gd`, Official service, save sessions and RPC authority. Reuse the current twelve-player dedicated coordinator and HTTPS/SQLite account service. Run the real multi-client integration probe and examine its assertions. Expand meaningful integration checks for map-owner departure/handoff, different maps, disconnect/reconnect, committed saves, trades, duplicate/replayed requests, expired sessions, incompatible versions and capacity. Validate sender ownership, payload bounds, finite numbers and rate limits at exposed boundaries. A modified client can currently invent rewards: identify what is fixed, what remains, and whether that blocks an open community beta. Do not describe client-simulated combat as server authoritative.

Prepare a repeatable Linux hosting package for a public IPv4 VM with UDP 24680 and HTTPS. Include configuration with a public hostname, normal certificate trust, persistent SQLite storage, two supervised services, clean shutdown, health checks, startup on reboot, log rotation, bounded logs, backups, a verified restore procedure, update/rollback and version compatibility. Handle certificate renewal and cross-service secrets deliberately. Keep private keys, databases, accounts and internal server keys out of Git and client packages. Inspect graceful shutdown and subprocess failures on Linux. Pin or constrain dependency versions reproducibly.

The likely region is Singapore; exact provider and budget require the user's answer. Do not buy cloud resources, change live player data or pretend hosting is complete without access and an independently reachable endpoint. Prepare the package and document the missing account/hostname steps. Keep localhost testing credentials separate from a public build. Show clear actionable connection errors in the game.

## Prompt 3: measured PC and mobile performance

Use the existing perf autoload, settings and benchmark scenes first. Profile with a real renderer; keep headless correctness testing separate. Capture baseline and candidate runs at identical revision-independent scenarios/settings, warmed up and repeated. Include town, outdoor map, interior, dungeon, dense combat and repeated map changes. Capture median/p95/p99 frame times, physics/process time, rendering context, RAM growth, draw calls, primitive counts, lights, awake animations and loading spikes. Measure multiplayer bandwidth/serialization at relevant player counts.

Target 60 FPS for a specified low-end PC at 720p/low and 30 FPS for a specified low-end Android device in efficiency mode. These are targets until measured on those devices. Preserve UI resolution while lowering 3D render cost. Optimize only demonstrated bottlenecks, checking light/shadow budgets, invisible actor animation, physics/AI work, transient allocations, effects/particles/corpses, minimap refresh, resource loads and network update work. Bound cleanup and retained resources across map transitions. Preserve gameplay, collisions, visible enemy warnings and save/network outcomes. Do not reduce all visuals blindly or use PC touch mode as proof of phone performance.

Test quality/mode changes and readable touch UI; background/resume and connection loss need device QA. Record any unavailable Android hardware and exact steps for the community device matrix. Provide before/after tables and rendered screenshots with engine, renderer, resolution and quality profile.

## Prompt 4: release verification, EXE/APK and main

After Codex reviews the milestone evidence and there are no unresolved ship-blocking failures in the intended beta scope, run the relevant complete suite, multi-client integration and final runtime captures. Inspect the diff for unintended save/progression changes, secrets, generated caches and unreviewed assets. Update the beta testing guide with known limitations, reproducible bug reporting, required ports/versions and device checks. Keep honest release language if combat remains client-simulated or public hosting is pending.

Export Windows EXE and Android APK using the installed Godot 4.7.2 and existing valid export/signing settings. Record commands, sanitized export logs, sizes, SHA-256, version, ABI and signature verification. Never log signing passwords. Smoke-test the fresh EXE; install/launch APK on an available authorized device or state that device launch is pending. Confirm client export contains no private server data or internal credentials and no development-only entrypoints. Do not replace an Android signing identity silently.

The user explicitly authorized pushing the finished work to main. Coordinate with Codex so only one party commits/pushes and no concurrent import/export runs corrupt caches. Preserve unrelated local work. Use normal Git commits/pushes without force; resolve remote advancement safely. Report exact pushed commit and absolute EXE/APK paths. Code checks, local multiplayer, public connectivity and real-device performance are separate gates: report each accurately.
