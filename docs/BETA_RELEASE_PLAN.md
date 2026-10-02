# Beyond Heroes beta release plan

Started: 2 October 2026 (Asia/Manila). Codex leads design, review and QA; the user's open Claude Code project is the primary programmer.

## Current evidence

- Checkout is `main`, tracking `origin/main` at `https://github.com/lemonquake/beyond-heroes.git`.
- Preserve pre-existing edits to `docs/CHEATS.md` and the four untracked female model files. Include them only after reviewing their intended purpose.
- Game uses Godot 4.7.2, GDScript, ENet multiplayer and existing Windows/Android export presets.
- Accounts and durable characters use a Python 3.12+ HTTPS service and SQLite. The dedicated Godot coordinator supports twelve players over UDP 24680. The account service defaults to TCP 8443.
- Combat and rewards currently trust client map owners. Hosting the coordinator elsewhere does not make combat server authoritative. Treat this as an explicit public beta release risk.
- Existing mobile mode enables efficiency settings, a light budget, animation sleeping and a 30 FPS limit. These need measurement, not replacement based on assumptions.
- Computer Use discovered Claude desktop but two window capture attempts timed out. No programming prompt has been delivered yet.

## Work and acceptance criteria

| Stage | Work | Evidence required |
| --- | --- | --- |
| Baseline | Run the existing service tests and Godot suite; inspect tests, benchmarks and content; document the current build tools. | Raw logs, exit codes, baseline revision, screenshots, reproducible commands. |
| Design and usability | Review launch, character creation, town, combat, inventory, settings, joining, disconnects and mobile controls. Fix the highest-impact problems. Preserve lore, saves, content and progression. | Before/after desktop and mobile screenshots; readable text; no clipped controls; first-session checklist. |
| Multiplayer | Test two clients and full capacity; different maps; map-owner departure; combat/loot; portals; trade; chat; disconnect/reconnect; stale sessions; full server; version mismatch. | Real client/process logs and assertions. Distinguish headless probes from interactive gameplay. |
| Hosted server | Prepare Linux setup with HTTPS, UDP, durable data, process supervision, backup/restore, health checks, version compatibility and rollback. | Validated configuration; dependency versions; restore test; public two-client connection when access exists. |
| Performance | Profile town, demanding outdoor map, interior, dungeon, dense combat and multiplayer. Fix measured bottlenecks. | Warm-up followed by repeated samples, median/p95/p99 frame times, CPU/GPU context, memory, draw calls, entities, loading and network traffic. |
| Release | Review changes and assets; rerun meaningful checks; export EXE/APK; verify signature/ABI/version and startup; commit and push to main. | Exact commit, clean relevant diff, export logs, SHA-256, artifact paths, remaining device checks. |

## Performance targets and test conditions

- Desktop low-quality target: stable 60 FPS at 1280x720 on a specified integrated-GPU machine; p95 frame time at most 16.7 ms is the aspirational gate to verify on that machine.
- Mobile efficiency target: stable 30 FPS on a specified low-end Android device; p95 frame time at most 33.3 ms after warm-up, with a longer thermal/battery session. Do not claim success from a PC running touch mode.
- Report uncapped render benchmarks separately from normal capped play. Headless frame rates cannot establish GPU performance.
- Record process/physics time, RAM growth, draw calls, lights, animation count and effects budget. Revisit several maps to find retained resources and memory growth.
- Preserve collision, enemy behavior, visible attack warnings, loot, network timing and UI readability while reducing rendering work.
- Cover touch sizes/safe areas, input focus, resume after backgrounding, suspend/disconnect, and ordinary laptop resolutions.

## Hosting decision

Use a Linux VM with public IPv4 and direct UDP support. Singapore is a candidate region for the Philippines, subject to measured latency. A starter size is 2 GB RAM and 1-2 vCPUs, to be validated under twelve-player load.

- DigitalOcean Basic: current official pricing lists 2 GB / 1 vCPU at US$12/month and 2 GB / 2 vCPUs at US$18/month: https://www.digitalocean.com/pricing/droplets
- Hetzner offers Singapore Linux VMs; IPv4 has a separate cost. Verify regional price before purchase: https://www.hetzner.com/cloud-singapore/ and https://docs.hetzner.com/cloud/servers/overview/
- Oracle Always Free is a possible cost-saving experiment. Its current official free tenancy limit is 2 Ampere A1 OCPUs / 12 GB; availability, idle reclamation and Godot ARM64 compatibility must be checked: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm

Do not purchase a server, create a paid subscription, or migrate live player data until the user provides the destination and spending authorization. Prepare all configuration and verification first. Keep the current server identity and player data private and intact. A web-only host cannot serve ENet UDP directly.

## Screenshots and handoff

Save fresh progress screenshots and machine-readable results in a dated evidence folder. Include desktop/mobile menu, gameplay, settings, multiplayer and any fixed defect. Every screenshot must identify the revision/profile and whether it is a scripted capture or interactive play.

Use `docs/CLAUDE_BETA_MASTER_PROMPTS.md` for programming instructions. Claude writes short milestone results to the evidence folder so Codex can review the actual diff, logs and screenshots without relying solely on its chat summary.

## Current status

Baseline QA is complete: 23 account tests pass; the full Godot suite has 122,903 checks and 34 failed assertions. Multiplayer integration assertions pass but raw logs contain lifecycle errors. Dense-combat median frame times reach 56-64 ms on the test PC. See `output/beta-20261002/QA_BASELINE_REPORT.md` for results and screenshots.

The local protocol mismatch was fixed with a backed-up managed restart; the server now reports protocol 16 and online. Separate Windows EXE and debug-signed Android APK baseline builds are compiled and checked. These are testing artifacts with unresolved failures, not the polished release. Draft Linux hosting configuration is in `server/deploy/`; no cloud host has been provisioned.

QA/design/hosting foundation changes are prepared for main. Claude prompt delivery remains blocked by Computer Use capture/input failures; the user has been given a brief instruction to paste. Hosting destination/budget and physical low-end device tests also remain pending. Gameplay polish and a verified release still require the programming stages.
