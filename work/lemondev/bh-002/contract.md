# Beyond Heroes — run bh-002 (systems development phase)

## Component contract

- **Run ID:** bh-002, started 2026-09-26. Baseline revision `368d816` (bh-001: core data systems, five maps, environment kit,
  audio, icons; 1418 headless checks passing). Rollback point = that commit.
- **User outcome:** `systems_development_phase.txt` — turn the data-layer slice into a playable ARPG: player controller,
  combat feel, enemies + AI, loot, 10-tier rarity, sets, shops, dialogue/NPCs, full UI (menu, hero select, HUD, character,
  inventory/equipment, skills, talents, shop, dialogue, settings, dev panel), hero + enemy models and animation sets,
  save v3, settings, QA tests.
- **Engine / platform / target:** Godot 4.4.1-stable Forward+ (`A:\Installer\Godot_v4.4.1-stable_win64.exe\`),
  Windows 10, RTX 4060 8 GB, 1920x1080 primary, UI also checked at 3840x2160 and 1280x720.
- **Tools:** Blender 5.2 (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`), Python 3.12 (numpy, PIL, scipy).
- **Asset sourcing:** in-house procedural generation (Blender Python, PIL/numpy, SVG). Third-party downloads need a
  per-file confirmation from the user in chat; none are requested in this run. `ASSET_CREDITS.md` stays authoritative.

## Components and ownership

| ID | Component | Owner | Files |
| --- | --- | --- | --- |
| C1 | Core rules: 10 rarity tiers, sets, affixes, item flags, stat additions, damage/status additions | Orchestrator (system) | `game/src/core/**`, `game/src/data/**` |
| C2 | Player controller, camera, combos, skills runtime, animation tree | Orchestrator (system) | `game/src/actors/**`, `game/src/combat/**`, `game/src/skills/**` |
| C3 | Enemies, AI, combat director, spawner, loot drops, elites, boss | Orchestrator (system) | `game/src/actors/enemy/**`, `game/src/world/spawn*`, `game/src/loot/**` |
| C4 | NPCs, dialogue, shops, world state | Orchestrator (system) | `game/src/npc/**`, `game/src/data/data_dialogue.gd`, `data_shops.gd` |
| C5 | UI code: menus, HUD, panels, tooltips, dev panel | Orchestrator (UI) | `game/src/ui/**` |
| C6 | Characters, weapons, animation library + `anim_meta.json` | Character builder (subagent) | `tools/blender/characters/**`, `game/assets/characters/**`, `game/assets/weapons/**`, `work/lemondev/bh-002/evidence/characters/**` |
| C7 | UI art: frames, panels, HUD art, rarity art, new icons, portraits | UI art builder (subagent) | `tools/ui_art/**`, `game/assets/ui/**`, `work/lemondev/bh-002/evidence/ui_art/**` |
| C8 | Save v3, settings, QA tests, integration | Orchestrator (integration) | `game/src/autoload/**`, `game/tests/**` |

Builders never run Godot on `game/` (the orchestrator imports assets). Builders never edit files outside their paths.

## Mandatory invariants (frozen; extend bh-001's list)

1. `DamagePipeline.compute` stays the only producer of damage numbers; displayed number == HP removed (shields tracked separately).
2. Crit x1.5 base before mitigation; 100 dmg crit = 150 pre-mitigation.
3. Equip/unequip restores every derived stat exactly (snapshot equality), including set bonuses.
4. XP carry-over across multi-level gains.
5. Status: single instance per id, documented refresh; removal leaves no modifiers behind.
6. Exactly ten rarity tiers in this order: Beginner, Common, Basic, Advanced, Licensed, Elite, Master, Mythical, Legendary, Aether.
7. Save v3 round-trip is exact (hero, inventory flags, equipment, skills, talents, teleporters, dialogue/NPC state, shop
   special stock, bosses, settings); v1/v2 migrate forward.
8. Attack damage is applied only inside animation-metadata hit windows (never at animation start).
9. AI: no invalid state transitions; at most N melee attackers engage simultaneously (combat director tokens).
10. UI never mutates simulation internals except through HeroData / controller intent methods.
11. No debug UI in normal play (F1 panel only with `--dev` or debug builds).

## Checks

- Headless unit/integration tests (`tools/run_tests.sh`) — extended for rarity, sets, flags, shops, dialogue, AI transitions,
  save v3, combo timing, skills.
- Soak: 10,000 steps at 60 Hz for knockback/status/AI with 100 agents (AI tick p95 < 0.8 ms total reported).
- Runtime captures with the real renderer at 1920x1080 (and 3840x2160 for UI) — menu, hero select, HUD states, panels.
- Performance: combat window per map, p95 frame time reported (target <= 16.67 ms on the RTX 4060).

## Benchmark

No commercial reference images are on disk (`references/` is empty). Visual/UI benchmark gates stay UNVERIFIED unless the
user supplies references; mechanics are judged against the explicit invariants above plus the spec's QA checklist.
Any visual self-check is labelled as such (not a blind review).

## Budget

8 build/review passes per component. No user time/cost ceiling stated.
