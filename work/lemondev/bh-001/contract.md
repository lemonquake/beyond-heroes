# Beyond Heroes — run bh-001 (vertical slice)

## Component contract

- **Run ID:** bh-001, started 2026-09-26.
- **User outcome:** a playable Godot action RPG vertical slice of *Beyond Heroes by Aljay Leodones*, per `game_implementation.txt`:
  Knight and Mage, character selection, stats, leveling, combat, multiple weapon types, equipment (exact slot layout),
  inventory, 8-element system, skill tree, talent tree, several enemy archetypes, elite, boss, loot, teleporters,
  town + dungeon + outdoor area (+ temple, boss arena), save/load, designed UI, VFX, animation, sound.
- **Scope exclusions for bh-001:** content expansion beyond the slice, controller rumble hardware testing, multiplayer,
  vendor economy beyond sell-ready data, quests.
- **Engine / platform / target:** Godot 4.4.1-stable (Forward+), Windows 10, RTX 4060, 1920x1080 primary; UI checked at 3840x2160.
- **Tools:** Godot 4.4.1 (`A:\Installer\Godot_v4.4.1-stable_win64.exe\`), Blender 5.2.1, Python 3.12 (numpy/PIL/scipy).

## Layout and ownership

| Path | Owner | Contents |
| --- | --- | --- |
| `game/src/**`, `game/tests/**`, `game/project.godot` | Orchestrator / System builder | All GDScript runtime, data definitions, tests |
| `game/assets/characters/**`, `game/assets/weapons/**`, `tools/blender/characters/**` | Character builder | Rigged humanoids, animation library, weapons |
| `game/assets/environment/**`, `game/assets/textures/**`, `tools/blender/environment/**`, `tools/textures/**` | Environment builder | Modular kit, props, breakables, tileable PBR textures |
| `game/assets/audio/**`, `tools/audio/**` | Audio builder | Synthesized SFX and music |
| `game/assets/ui/**`, `tools/ui_art/**` | UI art builder | SVG icons, emblem/logo art |
| `work/lemondev/bh-001/**` | Orchestrator | Contracts, evidence, ledger |

Asset contracts: `contracts/characters.md`, `contracts/environment.md`, `contracts/audio.md`, `contracts/ui_art.md`.

## Asset sourcing decision

The spec allows downloading free third-party assets, but each download needs a per-file confirmation from the user.
bh-001 therefore builds every asset in-house (Blender Python, numpy synthesis, hand-authored SVG, Godot shaders), which
the lemondev procedural default also prefers. `ASSET_CREDITS.md` records this and any later third-party additions.
System fonts (Book Antiqua, Palatino Linotype, Felix Titling, Georgia) are referenced through Godot `SystemFont`, not bundled.

## Benchmark

- The user supplied three reference images in chat (flooded cistern isometric cutaway, top-down crypt plan, top-down house
  battlemap). Direction extracted to `art_direction.md` and frozen as the visual criterion for maps. The images are not on disk,
  so a blind critic cannot receive them; the visual benchmark gate stays UNVERIFIED until they are saved to `references/`.
- Mechanics benchmark: explicit invariants from the spec's testing checklist (crit = 1.5x before mitigation, bonuses
  apply once and remove cleanly, XP carry-over, prerequisites enforced, knockback bounded, save round-trip exact,
  teleporter spawn correctness, UI numbers equal gameplay data, hit windows synced to animation metadata).

## Mandatory invariants (frozen)

1. One damage pipeline (`DamagePipeline.compute`) is the only producer of damage numbers; displayed number == applied HP loss.
2. Crit multiplier default 1.5, applied before mitigation; modifiable by stat `crit_damage`.
3. Movement speed hard cap 1.5x class base; attack/cast speed have diminishing returns and a hard animation-rate cap.
4. Equipment modifiers apply exactly once per equip and are fully removed on unequip (stat snapshot equality).
5. XP carry-over over multi-level gains; level cap respected.
6. Skill/talent prerequisites and point costs enforced; refund leaves no residue.
7. Status effects follow documented stacking rules (no duplicate instances, freeze immunity window).
8. Knockback/impact: finite velocities, per-hit impact cap, impact chain depth <= 1, no infinite loops.
9. Save v1 round-trip reproduces the character exactly; versioned migration path exists.
10. Teleporters place the player on the named spawn point of the destination map.
11. No debug UI in normal play (debug tools only with `--dev` or debug build + F1).

## Checks

- Headless unit/integration tests: `godot --headless --path game -s res://tests/run_tests.gd`.
- 10,000-step 60 Hz simulation soak for knockback/impact, status ticking, and AI state machine (100 agents, tick budget 0.8 ms p95 measured, reported).
- Runtime captures (real renderer) of each map, HUD states, menus at 1920x1080 and 3840x2160.
- Performance: 60-second representative combat window per map, p95 frame time <= 16.67 ms on the RTX 4060 at 1080p.

## Budget

Default 8 build/review passes per component. No user time/cost ceiling stated.
