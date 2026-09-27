# bh-010 contract — Hero expansion (passives, auras, 2 new classes), 10 new enemies, multiplayer polish, kid-friendly multiplayer guide

Run id `bh-010`, 28 September 2026. Engine Godot 4.7.2 (Jolt), Windows 10, RTX 4060, Blender 5.2
(`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`). Branch `main`, uncommitted working tree (user rule).
Baseline: HEAD 19d1de8 + uncommitted bh-008/bh-009 work. Baseline suite: **10,950 checks, 0 failures**
(`evidence/tests_baseline.txt`).

## Request (user, verbatim intent)
1. MASSIVELY expand Hero selection and Hero skills/abilities. The Warrior (our Knight) must get plenty of Passive skills
   like a Paladin in Diablo 2 (auras + passives + combat skills).
2. Add 2 more Hero classes (my call). Unique, but balanced so no class/skill becomes an abusable "meta".
3. Add 10 more enemy varieties with 3D models, animations and unique mechanics (e.g. Necromancer, Goblin Summoner).
4. Polish Multiplayer and crossplay (PC <-> PC, PC <-> phone).
5. Total documentation teaching multiplayer PC to PC, written so an 8-year-old can follow it.

## House rules (invariants for every builder)
- Never use Filipino words, names or folklore. Invent original fantasy names.
- Probes/captures that boot a hero must pass `--slot=93..99` (slots 0-2 are the player's saves).
- Never kill Godot by image name; stop only a PID you started (or use `timeout`).
- Tests/probes read the player's real settings.cfg; never write it.
- Work in the main working tree, no commits.
- Each builder writes ONLY its owned files (listed per component). Shared files are owned by the Orchestrator.

## Benchmark
- Mechanics: the user-named reference is **Diablo II's Paladin skill structure** (three skill tabs: combat skills,
  offensive auras, defensive auras; one aura active at a time, party-wide radius; ranked skills with synergies).
  Structural invariants are frozen below. No recorded D2 telemetry is available; numbers are our own.
- Visual: no commercial reference images were supplied (`references/` holds none for enemies/heroes). Visual gates stay
  **UNVERIFIED against a commercial benchmark**; builder contact sheets + in-engine captures are self-checks.

## Frozen roster

### Knight (existing class, D2 Paladin-style expansion)
Skill tree gets pages: **Combat** (existing 3 branches + new actives), **Auras** (Offense / Defense), **Disciplines** (passives).
- New actives: `zeal` Zeal (4-hit flurry), `blessed_hammer` Hallowed Hammer (spiralling Light hammer),
  `heavens_fist` Heaven's Fist (sky lightning at target + radial holy bolts).
- Auras (toggle, one active, pulse 1 s to allies incl. Tempos and co-op heroes, reserve mana):
  offense `aura_might` Aura of Might, `aura_cinders` Aura of Cinders, `aura_winter` Aura of Winter, `aura_fervor` Aura of Fervor;
  defense `aura_mending` Aura of Mending, `aura_defiance` Aura of Defiance, `aura_thorns` Aura of Thorns, `aura_clarity` Aura of Clarity.
- Passives (always on, ranked): `arms_mastery` Arms Mastery, `shield_mastery` Shield Mastery, `iron_skin` Iron Skin,
  `oathbound` Oathbound Resilience, `toughness` Toughness, `second_wind` Second Wind, `retaliation` Retaliation,
  `crusader_resolve` Crusader's Resolve.

### Mage (existing class)
Pages: **Spells** (existing + new), **Mastery** (passives).
- New actives: `blizzard` Blizzard (persistent ice storm), `flame_sentinel` Flame Sentinel (fire turret),
  `frost_orb` Frost Orb (slow orb shedding ice shards).
- Passives: `pyre_mastery` Pyre Mastery, `frost_mastery` Frost Mastery, `storm_mastery` Storm Mastery,
  `tide_stone_mastery` Tide & Stone Mastery, `inner_fire` Inner Fire, `mana_shield` Mana Shield, `spell_echo` Spell Echo,
  `arcane_precision` Arcane Precision.

### NEW class: Ranger (`ranger`) — bow/javelin hunter, resource **Focus** (0-100)
Focus builds while you fight from range (ranged hits, standing your ground away from enemies), drains when enemies are
in your face. At 60+ Focus you are **Steady** (+ranged critical chance). Deadeye spends it.
Pages: **Techniques** (Marksman / Wildcraft / Survival) and **Instincts** (passives).
- Actives: `power_shot` Power Shot (start), `multishot` Multishot, `frost_arrow` Frost Arrow, `blast_arrow` Blast Arrow,
  `arrow_rain` Arrow Rain, `deadeye` Deadeye, `storm_javelin` Storm Javelin, `snare_trap` Snare Trap,
  `blast_trap` Blast Trap, `vault` Vault, `hunters_mark` Hunter's Mark.
- Passives: `keen_eye` Keen Eye, `deadly_aim` Deadly Aim, `light_feet` Light Feet, `piercing_arrows` Piercing Arrows,
  `fleet_foot` Fleet Foot, `survivalist` Survivalist, `patient_hunter` Patient Hunter, `trapmaster` Trapmaster.
- Talent tree `ranger_talents`, keystones `r_sniper` Sniper's Creed, `r_windrunner` Windrunner, `r_traplord` Trap Lord.

### NEW class: Shadowblade (`shadowblade`) — dual daggers/claws, resource **Combo** (0-5 pips)
Builders add pips (crits add 2); finishers spend all pips. At 5 pips you are **Poised**: the next finisher always crits.
Pips fade out of combat.
Pages: **Techniques** (Assassination / Shadow Arts / Venom & Traps) and **Disciplines** (passives).
- Actives: `twin_fang` Twin Fang (start), `venom_strike` Venom Strike, `shadow_step` Shadow Step, `fan_of_knives` Fan of Knives,
  `crippling_star` Crippling Star, `eviscerate` Eviscerate, `death_blossom` Death Blossom, `smoke_veil` Smoke Veil,
  `blade_sentinel` Blade Sentinel, `dread_mark` Dread Mark, `quickstep` Quickstep.
- Passives: `blade_mastery` Blade Mastery, `lethality` Lethality, `evasion` Evasion, `venomcraft` Venomcraft,
  `ruthless` Ruthless, `shadow_discipline` Shadow Discipline, `opportunist` Opportunist, `fleet_step` Fleet Step.
- Talent tree `shadowblade_talents`, keystones `s_deathmark` Death Mark, `s_phantom` Phantom Veil, `s_plague` Plaguebringer.

### 10 new enemies (+2 helpers)
| id | Name | Family / role | Signature |
|---|---|---|---|
| `necromancer` | Necromancer | undead / summoner caster | raises fresh corpses as Risen; bone spears; bone ward on allies |
| `goblin_summoner` | Goblin Summoner | goblin / support | calls skulkers through a smoking burrow; frenzy drum; hex bolts; cowardly |
| `orc_shaman` | Orc Shaman | orc / support | plants a destroyable War Totem (pulses Empowered); lightning; bloodlust |
| `frost_revenant` | Frost Revenant | undead / elite melee | chill aura; ice shard fan; frozen ground; shatters on death |
| `plague_bloater` | Plague Bloater | corrupted / brute | bile spew cone; bursts into a toxic cloud on death that also hurts monsters |
| `bandit_bombardier` | Bandit Bombardier | bandit / artillery | lobbed fuse bombs; at low HP lights its powder keg and charges |
| `mire_troll` | Mire Troll | beast / brute | regenerates fast unless recently burned; mud hurl slows |
| `rune_golem` | Rune Golem | construct / tank | rune core cycles element: immune to it, weak to its opposite |
| `broodmother` | Broodmother | beast / spider | web spit roots; poison bite; lays spiderlings |
| `treasure_mimic` | Mimic | construct / ambusher | looks like a chest until you come close; tongue pull; rich loot |
| `spiderling` | Spiderling | helper (broodmother model, small) | |
| `war_totem` | War Totem | helper (stationary) | |

## Components (one owner each)
| # | Component | Owner | Files |
|---|---|---|---|
| C1 | Skill framework: passives, auras, synergies, pages, new behaviours, class resources Focus/Combo, statuses | Orchestrator | `skill_def.gd`, `tree_state.gd`, `tree_def.gd`, `hero_data.gd`, `skill_runner.gd` (+ new `skill_runner_ext.gd`), `class_resource.gd`, `player.gd`, `status_rules.gd`, `stat_defs.gd`, `stat_calculator.gd`, new `src/skills/*.gd` |
| C2 | Class & skill data (4 classes) + talents + balance | Orchestrator | `data_classes.gd`, `data_skills.gd` (+ new data files), `data_talents.gd`, `data_items.gd` (starting gear) |
| C3 | Hero selection + skills window + HUD | Orchestrator | `hero_select.gd`, `skills_window.gd`, `tree_view.gd`, `hud.gd`, `tips.gd`, `character_preview.gd`, `main_menu.gd` |
| C4a | Enemy models set A (humanoid): necromancer, goblin_summoner, orc_shaman, frost_revenant, plague_bloater | Builder A | `tools/blender/characters/enemy_<id>.py`, `game/assets/characters/<id>.glb(.import)`, `work/lemondev/bh-010/evidence/enemies_a/` |
| C4b | Enemy models set B (humanoid): bandit_bombardier, mire_troll, rune_golem | Builder B | same pattern, `evidence/enemies_b/` |
| C4c | Creature models: broodmother (8-leg rig), treasure_mimic, war_totem | Builder C | `tools/blender/creatures/build_<id>.py`, GLBs, **creature_meta.json (merge only)**, `evidence/creatures/` |
| C5 | Hero models: ranger, shadowblade (+ idle_ranger, idle_shadowblade fidgets) | Builder D | `char_ranger.py`, `char_shadowblade.py`, `build_chars.py` (CHARACTERS entries only), `lib_idles.py` (2 new clips only), `anim_meta.json` (2 added keys only), GLBs, `evidence/heroes/` |
| C6 | UI art: ~70 skill icons, talent icons, class crests, portraits, tree backdrops, status icons | Builder E | `tools/ui_art/*` new modules, `game/assets/ui/**` new files only, `evidence/ui_art/` |
| C7 | Enemy runtime: defs, AI abilities, traits, spawns, bestiary, loot | Orchestrator | `data_enemies.gd`, `enemy.gd`, `enemy_def.gd`, `lob.gd`, map builders, `data_guide.gd` |
| C8 | Multiplayer polish + crossplay | Orchestrator | `net.gd`, `net_avatar.gd`, `multiplayer_window.gd`, new `net_*.gd` |
| C9 | Kid-friendly multiplayer guide | Orchestrator | `docs/MULTIPLAYER_GUIDE.md`, in-game help page |
| C10 | Tests + balance harness | Orchestrator | `tests/unit/test_skills.gd`, `test_balance.gd`, `test_enemies2.gd`, `test_net.gd`, tools |

## Acceptance gates
- Headless suite 0 failures; `compile_all` 0 failed; new tests: every skill/passive/aura resolves, has an icon, a valid
  behaviour, sane params per rank; every tree node reachable; saves round-trip for all 4 classes; old saves load.
- **Balance gate (anti-meta)**: `test_balance.gd` simulates each class with class starting gear + an equal-budget build at
  levels 1/10/20/30 against a standard dummy: sustained single-target DPS, 6-target AoE DPS, effective HP. Frozen bands:
  every class's *power score* (sqrt(single DPS * AoE DPS) * sqrt(EHP)) within **±20 %** of the mean at each level; no
  single active skill's damage-per-mana-second more than **2.0x** the class median; no passive gives >35 % of a class's
  total damage at max rank. Keystones exclusive.
- Combat bot run per class on the same map/seed: no deaths on Veteran at level 5, clear time within ±35 % of the mean.
- Enemies: all 12 defs load, GLBs import with every listed clip, each trait exercised by a probe (raise, summon, totem,
  frost aura, bloater burst, fuse charge, troll regen/fire stop, rune shift immunity, web root, mimic ambush).
- Multiplayer: two-instance probe (host + client) passes join by code, new classes visible as avatars, aura buff crosses
  the network, a new enemy's summon replicates, ping shown; protocol mismatch refused with a clear message.
- Captures: hero select (4 classes) at 1920x1080 and 3840x2160; skills window pages; in-game new enemies; auras.
- Budget: max 8 build/review passes per component.
