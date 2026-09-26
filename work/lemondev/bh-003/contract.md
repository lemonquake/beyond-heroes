# Beyond Heroes — run bh-003 (enemies, town interiors, guilds & tiers, lore)

## Component contract

- **Run ID:** bh-003, started 2026-09-26. Baseline revision `51706c7` (bh-002 C4/C5 + Godot 4.4 fix; 2971 headless
  checks passing on Godot 4.4.1 Linux). Rollback point = that commit.
- **User request:** (1) make sure the game on the user's PC is up to date; (2) design all enemies with unique features
  and animations, hit effects, death animations, blood hit effects, corpse decay; (3) full interior design for all town
  structures (houses, taverns) with unique NPCs whose dialogue is rooted in the lore; (4) an Inn that heals for a fee;
  (5) a comprehensive lore MD that all agents follow (`docs/LORE.md`), including hero tiers E..SSS with emblems,
  level requirements and equip privileges, 2 guilds with banners and perks, the world Jre, Salmonan / Malasugue, the
  Holy War and the ancient creatures.
- **Engine / platform:** Godot 4.4.1 (the user's last fix targeted 4.4; `project.godot` also lists 4.7 features, so no
  4.5+-only API may be used). Windows 10 + RTX 4060 on the user's side; this container: Linux, Godot 4.4.1 headless,
  Xvfb + Mesa software GL for real-render captures (images valid, frame times NOT representative).
- **Tools here:** `bpy` 4.4 pip module (Blender as a Python module; the user's Blender is 5.2 — scripts must stay
  compatible with both), Python 3.11 + numpy<2 + PIL.
- **Asset sourcing:** in-house procedural generation only. No downloads.

## Components and ownership

| ID | Component | Owner | Files |
|---|---|---|---|
| L | Lore bible | Orchestrator | `docs/LORE.md` |
| P | Shared character pipeline (registry, clip subsets, palette materials, death/devour clips, preview tool) | Orchestrator | `tools/blender/characters/{build.py,build_chars.py,bh_materials.py,bh_anim.py,lib_actions.py,preview_enemy.py}` |
| E1 | Enemy models: undead + construct | Builder A | `tools/blender/characters/enemy_{hollow_soldier,bonewarden,grave_archer,boss_warden,aether_sentinel}.py`, matching GLBs |
| E2 | Enemy models: cult, corrupted, bandits | Builder B | `enemy_{ashen_cultist,ashen_acolyte,ghoul_brute,shade_stalker,bandit_cutthroat,bandit_marksman}.py`, GLBs |
| E3 | Enemy models: greenskins, wolf, wisp | Builder C | `enemy_{goblin_skulker,orc_reaver,ogre_crusher}.py`, `tools/blender/creatures/**`, `dire_wolf.glb`, `aether_wisp.glb`, `game/assets/characters/creature_meta.json` |
| T | Townsfolk models | Builder D | `tools/blender/characters/town_*.py`, matching GLBs |
| A | Buildings + interior props | Builder E | `tools/blender/environment/assets_interior.py`, `assets_town2.py`, one import line in `build_assets.py`, new GLBs in `game/assets/environment/` |
| U | UI art: tier emblems, guild banners, NPC portraits | Builder F | `tools/ui_art/bh003_*.py`, `game/assets/ui/tiers/**`, `game/assets/ui/guilds/**`, `game/assets/ui/portraits/<new>.svg` |
| R | Enemy runtime: hit FX by material, blood, deaths, corpse decay, signature traits, new enemy defs | Orchestrator | `game/src/actors/**`, `game/src/vfx/**`, `game/src/data/data_enemies.gd`, `game/src/world/spawner.gd` |
| G | Guilds & tiers: data, HeroData, promotion, perks, equip gating, save, HUD/character UI | Orchestrator | `game/src/data/data_guilds.gd`, `game/src/core/**`, `game/src/ui/**` |
| I | Interiors, doors, town layout changes, NPC roster + dialogue, Inn | Orchestrator | `game/src/world/**`, `game/src/npc/**`, `game/src/data/data_npcs*.gd`, `data_maps.gd` |
| Q | Tests, integration, evidence | Orchestrator | `game/tests/**`, `work/lemondev/bh-003/**` |

Builders never run Godot on `game/` (the orchestrator imports assets), never edit files outside their paths, and
never commit.

## Mandatory invariants (extend bh-002's list, which stays in force)

1. `DamagePipeline.compute` remains the only producer of damage numbers; displayed number == HP removed.
2. Attack damage only inside animation-metadata hit windows (enemy attack clips keep measured `hits`).
3. Tier gating: an item whose rarity requires a higher tier can never be equipped (check + equip paths), and existing
   saves without guild data load as Unranked with no loss of equipped items (already-equipped gated items stay
   equipped but are flagged, never destroyed).
4. Save v3 round-trip stays exact and now includes guild id, tier, rested buff state; v1/v2 still migrate.
5. Inn: resting costs exactly the quoted fee (after guild discount), fully restores HP/mana, removes harmful statuses,
   never runs with insufficient gold.
6. Doors: entering and leaving an interior returns the hero to the matching door outside; no duplicate players, NPCs,
   listeners or maps after repeated cycles.
7. Corpses: bounded count (oldest decays first), every corpse node freed after decay; blood decals bounded.
8. Blood/gore can be turned off in Settings (default on); with it off no red blood is spawned.

## Checks

- Headless suite (`tools/run_tests.sh` with `GODOT` pointing at 4.4.1) extended for: guild join/promote/gating,
  save round-trip of the new fields, Inn fee/heal, door cycles, corpse/decal bounds, every enemy def loads its model
  and every attack anim exists in that model, dialogue graphs (every node reachable, every `next` resolves, every
  condition/action known).
- Real-render captures (software GL): enemy line-up, death/decay sequence, each interior, HUD tier emblem, guild
  halls, dialogue with a new NPC.
- Blender-side validation per model: tri budget, bone count, clip list, and preview sheets.

## Benchmark

`references/` is empty and the user supplied no reference images for this run. Visual quality gates therefore stay
**UNVERIFIED** against a commercial benchmark; builders' preview sheets and orchestrator captures are self-checks, not
blind reviews. Mechanics are judged against the invariants above.

## Budget

8 build/review passes per component; no user time/cost ceiling stated.
