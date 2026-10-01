# bh-028 plan and handoff — Evasion fixes, curses, level HP, celestial orbs, special dungeons

Branch: `lemonquake/exciting-albattani-lzv83l`. This file is the working plan **and** the handoff: every phase lists
what is done, where the code lives and how to verify it. If you pick this up from another agent, read
"Status at a glance", then the first phase that is not ✅.

## Status at a glance

| # | Phase | Status |
|---|---|---|
| 0 | Research, tooling, this plan | ✅ done |
| 1 | Evasion investigation + fixes | ✅ done |
| 2 | +50 HP per level (old and new saves) | ✅ done |
| 3 | Level 40+ enemy curse (Hex of Frailty) | ✅ done |
| 4 | Celestial orbs: Sora, Luna, Sol, Airah | ✅ done |
| 5 | Five special dungeons after Kethrax | ✅ done |
| 6 | Tests, screenshots, changelog, push | ✅ done |

Legend: ✅ done · ⏳ in progress · ☐ not started. Update this table and the phase notes as you go.

## Environment notes (for the next agent)

- Godot **4.7.2** (the project's version) is not installed system-wide. Download it to the scratchpad:
  `https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip`
  then `godot --headless --path game --import` once (≈3 min).
- Python texture tools need `pip install numpy pillow`.
- Blender is not available in the cloud container: new icons are rendered by Godot (see phase 4).
- Run a few suites: `godot --headless --path game res://tests/run_tests.tscn -- --only=test_bh028,test_stats`.
  The full suite takes ~15 min and had **36 pre-existing failing checks** on `main` (docs/HANDOFF_bh-027.md).
- Screenshots: `xvfb-run -a godot --rendering-driver opengl3 --path game --resolution 1600x900 res://tests/tools/capture_bh028.tscn`.

---

## Phase 1 — Evasion: why it is inconsistent, and the fix

### Investigation (evidence: `work/lemondev/bh-028/evidence/evasion_probe.txt`, tool `tests/tools/probe_evasion.tscn`)

Formula (`DamagePipeline.evade_chance`): `min(65%, Evasion / (Evasion + attacker Accuracy))`. Hero Evasion = 2 × AGI
× (1 + increased) × more. Monster Accuracy = base 28–64 + 4 per level.

Findings:

1. **The cap is reached at level ~10 and never left.** A Ranger or Shadowblade with the class's evasion passives
   (Light Feet / Evasion skill, Elusive / Blur talents) has 266–377 Evasion at level 10 and 2,600–4,000 at 120,
   while monsters have 70–540 Accuracy. Every row of the probe shows exactly 65%, so every extra passive rank or AGI
   point does nothing that the player can see, and the character sheet always says 65%.
2. **A third of monster damage — two thirds of boss damage — can never be evaded.** Only `melee`, `dash`, `charge`,
   `projectile`, `chain` and `tongue` attacks are evadable (`Enemy._attack_request`). `aoe` (89 attacks), `pools`,
   `strikes`, `beam`, `mines`, `gaze`, plus every trait hit (`enemy_traits_x/_ext` set `evadable = false`) always
   land. Weighted by how often they are picked: 68% of pack attacks and only 33% of boss attacks are evadable. Higher
   levels mean more bosses, champions, elites with three abilities (level 50+) and caster reinforcements, so the
   share of hits Evasion ignores grows — that is the "inconsistent at higher levels" feeling, while the sheet keeps
   promising 65%.
3. **Hunter (Ranger) passives that never fire:**
   - *Second Nature* (and the Shadowblade's *Slip*, the Knight talent, the Serpent Veil set): "Evading an attack
     restores Mana" only worked for dodge-roll i-frames. `Actor._on_evaded` is never overridden by `Player`, so a
     real Evasion roll restored nothing.
   - *Windrunner* keystone: "Moving builds Focus as if you stood calm" — the `windrunner` flag is never read.
   - *Hunter's Calm*: "Focus no longer fades out of combat" — `focus_hold` is never read (hold is always `false`).
   - *Phantom Veil* (Shadowblade keystone): "Dodging cloaks you in Stealth" — `dodge_stealth` is never read.
4. Smaller: the sheet's Evade Chance tooltip says "cap 50%" (it is 65%).

### Fix (design)

- **Graze**: area attacks (aoe/strikes/pools/beam/mines/gaze and trait blasts) become evadable *as a graze*: same
  formula but Accuracy counts ×4 and the cap is 45% (`DamagePipeline.GRAZE_ACC_FACTOR`, `GRAZE_CAP`). This is where
  Evasion above the direct-hit cap keeps paying off, so passive ranks and AGI matter at every level.
  `DamageRequest.graze` marks such hits (sent over the network too).
- Character sheet: **Evade Chance** (direct hits) and new **Graze Chance** (area hits) against a same-level
  reference monster; tooltip text fixed.
- Dead passives wired: `Player._on_evaded` → evade_mana (+ Luna orb heal, phase 4); `windrunner` and `focus_hold`
  passed to `ClassResource.tick`; `dodge_stealth` applies `stealth` on dodge.

### Done / notes
- `DamagePipeline.GRAZE_ACC_FACTOR/GRAZE_CAP`, `DamageRequest.graze` (in `NetCodec.REQ_FIELDS`).
- `Enemy.DIRECT_KINDS`; `_attack_request` marks everything else `graze`. Trait blasts (`enemy_traits_ext._req`), storm
  strikes, sapper mines, beams, pool ticks and projectile explosions from monsters graze too.
- `Actor.receive_hit`: monsters never graze (friendly-fire blasts like the Plague Bloater's still hurt them).
- `Player._on_evaded` / `_evade_rewards`; Focus tick gets `focus_hold` and `windrunner`; `dodge_stealth` on dodge.
- Sheet: `graze_chance` (StatCalculator, StatDefs, CharacterWindow).
- Probe after the fix: every level shows 65% evade / 45% graze with full passives, 28–45% graze without them, so
  passive ranks and Agility now visibly matter at every level.
- Regression check vs. the baseline worktree (same suites): identical failures (`test_enemies2` 8,
  `test_dungeon_growth` 1 — both pre-existing).

---

## Phase 2 — +50 HP per level for every hero

- `StatCalculator.LEVEL_UP_HP := 50.0`, added as its own line in Maximum HP: `Level-up bonus (level N): +50 × (N-1)`.
- It is computed from the level every time stats are built, so **old saves get it on load with no migration** and
  new heroes get it as they level. Tempos/guild fighters built by StatCalculator also get it (they mirror heroes).
- Test: an old-format save at level 40 has +1,950 HP over the pre-change formula.
- ✅ Done: `ClassDef.level_up_hp` (default `StatCalculator.LEVEL_UP_HP` = 50). Tempo shells set it to 0 because they
  mirror half of the hero's HP, bonus included (`test_tempos` caught this).

---

## Phase 3 — Level 40+ curses: Hex of Frailty

- New status `hex_frailty` (StatusRules): 5 s, debuff, **-20% all elemental resistances, -15% physical
  resistance, 40% less Evasion**. Cleansable like other curses. Icon: `cursed`.
- New enemy attack kind `"hex"` added at runtime by `Enemy` to every monster of **level ≥ 40** that has a normal
  attack list (not totems/mimics/summons with no damage): a short cast with a purple sigil under the hero; if the
  hero is still in it when it lands, the hex applies. It can be dodged (i-frames) and grazed like any area attack.
  Cooldown 14–18 s; casters/bosses use it more often. Data: `DataEnemies.HEX_ATTACK`.
- Monsters' own `cursed` affix is unchanged.
- ✅ Done: `StatusRules.DEFS.hex_frailty` (`fixed_duration`), `StatusController.apply` honours it,
  `DataEnemies.HEX_LEVEL / hex_attack / extra_attacks`, `Enemy.extra_attacks` (joins `_choose_attack`),
  violet telegraph + "Hexed!" popup in `Enemy._telegraph_aoe` (`hex`, `tele_color` keys). Cleansable.

---

## Phase 4 — Celestial orbs (Sora, Luna, Sol, Airah)

Four new crystal families in `DataCrystals.FAMILIES` (same four grades as the other crystals: Fragment, Shard,
Crystalline, Orbital — the socket, shop, naming and drop systems are built on four grades, so Crystalline is kept).

| Orb | Weapon | Armour | Jewellery | Passive |
|---|---|---|---|---|
| **Sora** (sky) | +Accuracy (Hit Rate), +Knockback (impact strength) | +all resistances | +all resistances, +status res. | — |
| **Luna** (moon) | +Dark damage, +crit damage | +increased Evasion, +Dark res. | +Mana regen, +cooldown recovery | Armour: *Moonveil* — evading heals % max HP |
| **Sol** (sun) | +Light and Fire damage | +Maximum HP, +HP regen | +healing, +Light damage | Weapon: *Sunflare* — crits burst Light on nearby foes |
| **Airah** (wind) | +Wind damage, +attack speed | +move speed, +Wind res., faster dodge | +cast speed, +dodge distance | Jewellery: *Tailwind* — dodging hastes you |

- Names: `CrystalNames` gets single-family tiers, 4 epithets and the 38 new hybrid names (12 families → 66 pairs).
- Drops: bosses level 40+ can roll celestial orbs (`DataCrystals.roll_drop`), special-dungeon bosses always drop one
  of their dungeon's orb. Socket Specialists sell them (expensive).
- Icons: rendered in Godot by `tests/tools/render_orb_icons.tscn` (raw gems → `work/lemondev/bh-028/scratch/orb_raw`),
  finished by `tools/ui_art/bh028_orb_icons.py` → `assets/ui/icons/crystals/<family>_<grade>.png`. Preview:
  `work/lemondev/bh-028/evidence/orb_icons.png`. Socket sprites: `tools/ui_art/bh022_sockets.py` (only the 16 new
  files were kept; regenerating the old ones changes bytes under a different PIL).
- ✅ Done: `DataCrystals` (`CELESTIAL`, `COMMON`, `is_celestial`, `roll_drop(..., favour)`), `CrystalNames`,
  `DataShops.crystal_stock`, `Loot` (dungeon `orb` favour + guaranteed orb from special-dungeon lords),
  `Player._crit_sunflare`. Tests `test_bh018`/`test_bh022` counts updated (48 crystals, 66 pairs).

---

## Phase 5 — Five special dungeons (after Kethrax)

- **Unlock**: a portal on Malasugue's waypoint terrace to the new hub map **The Sundered Reach** (`sundered_reach`),
  locked by `boss_kethrax_defeated`. The flag is read live, so old saves where Kethrax is dead have it open at once.
- **Requirement**: each dungeon gate needs **Class A** (tier rank ≥ 5): `Teleporter.min_tier`. Recommended levels
  80–120 on the gate signs.
- Dungeons (`DataDungeonsSpecial`), tier 6 "Ascendant", 10–15 floors, no DungeonGrowth extra floors:

| id | Name | Theme / texture | Floors | Levels | Orb |
|---|---|---|---|---|---|
| `prismheart` | The Prismheart Hollows (Crystal) | `prism` / `crystal_facet` | 10 | 80–89 | Sora |
| `underworld` | The Underworld of Mourning | `underworld` / `obsidian_soul` | 12 | 86–97 | Luna |
| `aetherreach` | The Aether Reach | `aether` / `aether_opal` | 13 | 92–104 | Airah |
| `eclipse` | The Eclipse Vault | `eclipse` / `moonstone` | 14 | 100–112 | Luna |
| `solarium` | The Drowned Solarium | `solar` / `sunstone` | 15 | 106–120 | Sol |

- Plans: `tools/dungeon_gen/gen_plans.py --special` → `game/src/data/data_dungeon_plans_special.gd` (bigger
  floors, more storeys and basins than bh-013).
- Each theme has its own centrepiece in `dungeon.gd` (`_special_centrepiece`): giant glowing crystal clusters,
  soul-fire pillars over a ghost river, floating aether islands, a black moon over the basin, a sun orb.
- Bosses: five new data-driven bosses in `DataEnemiesSpecial` (existing models, new tint/scale/attacks).

---

### Phase 5 handoff — exact state and next steps

Done (committed):
- **5a Plans**: `tools/dungeon_gen/gen_plans.py --special` (`SPECIAL_SPECS`) → `game/src/data/data_dungeon_plans_special.gd`
  (`DataDungeonPlansSpecial.PLANS`, 64 validated floors: prismheart 10, underworld 12, aetherreach 13, eclipse 14,
  solarium 15; last floor = boss sanctum, second-to-last = champion floor, rest = Seal Keeper floors).
- **5b Textures**: `tools/textures/gen_textures.py` sets `crystal_facet`, `obsidian_soul`, `aether_opal`, `moonstone`,
  `sunstone` → `game/assets/textures/<set>_{albedo,normal,rough}.png`. Preview `work/lemondev/bh-028/evidence/special_textures.png`.
  Open the project once in Godot so their `.import` files are generated.

To do, in this order (all designs are decided above; findings from reading the code):
1. **`game/src/data/data_dungeons_special.gd`** (`class_name DataDungeonsSpecial`), same shape as `DataDungeonsX`:
   - `THEMES` for `&"prism"`, `&"underworld"`, `&"aether"`, `&"eclipse"`, `&"solar"` (copy a `DataDungeonsX.THEMES`
     entry; `"stone": {"BH_Stone": ["crystal_facet", Color(1,1,1)], "BH_StoneDark": ["crystal_facet", Color(0.55,0.55,0.6)]}`
     etc. — MaterialLibrary picks textures by set name).
   - `DRESS`, `CLUTTER`, `GATE_DRESS` per theme, using only kit names already used in `DataDungeonsX.DRESS`
     (crystal_pylon, ice_crystal_large/small, obelisk_corrupted, floating_rock, candles_cluster, statue_knight, ...).
   - `LIST`: per dungeon `name, theme, tier: 6, special: true, min_tier: 5, orb (sora/luna/airah/luna/sol),
     material, surface {"map": &"sundered_reach", "pos", "yaw", "place"}, blurb, levels (spread 80–89 / 86–97 /
     92–104 / 100–112 / 106–120 over the floors, last floor [hi, hi]), pools a/b/seal, music, ambience, footstep,
     reverb, miniboss, boss, usurper, power {"hp": 1.5, "damage": 1.3}`. Suggested pools:
     prismheart a [prism_sentinel, star_mote, mirror_knight, aether_wisp] b [rune_golem, shellback_grinder, aegis_acolyte, astral_duelist];
     underworld a [forsaken_legionnaire, hollow_soldier, gloomwraith, shade_stalker] b [forsaken_chainguard, necromancer, gravecaller, bloodbinder, ghoul_brute];
     aetherreach a [aether_wisp, aether_sentinel, storm_herald, astral_duelist] b [riftcaller, clockwork_sentry, aegis_acolyte, rune_golem];
     eclipse a [shade_stalker, mirage_weaver, gloomwraith, astral_duelist] b [void_seer, mirror_knight, riftcaller, soulbound_twin];
     solarium a [cinder_imp, ashen_cultist, drowned_deckhand, slag_hound] b [magma_golem, brinecaller, forge_thrall, ashen_acolyte, barnacle_hulk].
   - `static func list()` merging `DataDungeonPlansSpecial.PLANS` as `floors` (like `DataDungeonsX.list()`).
2. **`DataDungeons`**: merge `DataDungeonsSpecial.list()` in `defs()`; `theme()` also looks in
   `DataDungeonsSpecial.THEMES`; add `is_special(id)`; `map_defs()` and `floor_def()` must not create growth floors
   for special dungeons; `DataDungeonsX.TIER_NAMES` append `"Ascendant"` and let `tier_name/tier_stars` handle 6.
   `dungeon.gd` (`DRESS.get`, `CLUTTER.get`) and `map_builder.gd dungeon_gate` (`GATE_DRESS`) need a third fallback
   to the special dicts.
3. **`DungeonGrowth`**: for special dungeons `for_hero` → `extra = 0`; `levels()` returns the authored levels;
   `pool()` returns the original pool.
4. **Spawner** (`world/spawner.gd populate`): if special, `s.difficulty = difficulty.duplicate()` with
   hp × power.hp, damage × power.damage ("very strong").
5. **Bosses** `game/src/data/data_enemies_special.gd`: duplicate existing boss EnemyDefs (no boss-id-specific code
   exists, verified) with new id/name/tint/model_scale/hp×1.6/damage×1.25/lore and register them at the end of
   `DataEnemies.build()`: prismheart←prism_colossus "Seraphel, the Prismheart"; underworld←hollow_dark
   "Morrowgaunt, King Below"; aetherreach←voltaric "Zephyrion, the Aether Heart"; eclipse←astrarch
   "Nocthea, the Eclipsed Star"; solarium←forgemaster "Solmara, the Drowned Sun".
6. **Class A lock**: `world/teleporter.gd` add `var min_tier := 0`; `is_locked()` also true when
   `Game.hero.tier < min_tier`; hint "Requires Class A". `MapBuilder.dungeon_gate` sets `t.min_tier` from the def.
7. **Hub map** `sundered_reach`: `game/src/world/maps/sundered_reach.gd` (copy the structure of
   `weeping_causeway.gd`: environment, terrain or floor tiles, five `dungeon_gate(id, pos, yaw)` calls via
   `DataDungeons.gates_on(def.id)`, spawn `arrival` + a return teleporter to `sanctuary/waypoint`). Register in
   `DataMaps.build()` (`waypoint: false`) and add DataIsland entries like `weeping_causeway` (lines ~23, 33, 149, 364).
8. **Malasugue portal**: in `sanctuary.gd _terrace()` add
   `teleporter(&"sanctuary_rift", Vector3(7.5, TERRACE_Y, -24.5), &"sundered_reach", &"arrival", "The Sundered Reach", 0.0, true, &"boss_kethrax_defeated", "The rift is sealed. It opens once Kethrax falls.")`
   (check the `teleporter()` signature in map_builder.gd). The flag is read live → old saves with Kethrax dead are open.
9. **Centrepieces** in `dungeon.gd _light_and_dress()` like the orrery armillary block: per special theme, emissive
   SphereMesh/crystal clusters over the basin centre (sun orb for solar, black moon with silver rim for eclipse,
   floating rocks + Spinner for aether, teal soul-fire columns for underworld, big crystal_pylon ring for prism).
10. Tests in `test_bh028.gd`: 5 special dungeons, 10–15 floors, levels within 80–120, gates on sundered_reach,
    min_tier 5, no growth floors, portal locked until `boss_kethrax_defeated`; run `test_dungeon_growth`, `test_maps`,
    `test_island`, `test_bh013` (they iterate every dungeon). Then screenshots (`capture_bh028.tscn`, see
    `capture_bh013.gd` / `capture_depths.gd` for how floors are loaded and captured), CHANGELOG BH-028.

## Phase 6 — Wrap-up
- New suite `game/tests/unit/test_bh028.gd`.
- Screenshots in `work/lemondev/bh-028/evidence/`.
- `docs/CHANGELOG.md` (BH-028) and this file's status table.

---

## Completion notes (merged on `main`)

- The same day, a second bh-028 effort landed on `main`: the combat budget and the Sand Arena (docs/COMBAT_SCALING.md,
  `CombatBudget`, `ArenaGrounds`, protocol 14). Its suite is `test_bh028_arena.gd`; this plan's checks stay in
  `test_bh028.gd`. Vitality (+16 HP per level after 5) and the +50 HP level-up bonus stack; Tempo shells skip both
  (`ClassDef.vitality = false`, `level_up_hp = 0`).
- Phase 5 as built:
  - `DataDungeonsSpecial`: themes, dressing, pools, champions and Usurpers. `list()` spreads `span` over the floors and
    fills in the tier, `special`, `min_tier`, `power` and the gate spot.
  - `DataEnemiesSpecial`: the five lords, copied from their template bosses with ×1.6 health and ×1.25 damage.
  - `DataDungeons`: `is_special`, `max_extra`, `min_tier`. `DungeonGrowth` keeps the special dungeons' floors, levels
    and pools fixed. The Spawner multiplies difficulty by `POWER`. `Teleporter.min_tier` / `tier_locked` /
    `lock_text` enforce the Class A lock.
  - `sundered_reach.gd` hub. The `sanctuary_rift` teleporter is locked by `boss_kethrax_defeated`.
  - `DataIsland`: the `sr_landing` place, the dungeon places and the `sundered_rift` / `<id>_gate` links. The Reach
    draws at Malasugue on the atlas.
  - `dungeon.gd _special_centrepiece`.
- Evidence: `tests/tools/capture_bh028_special.tscn` → `work/lemondev/bh-028/evidence/special/`.
