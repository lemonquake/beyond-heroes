# bh-028 plan and handoff — Evasion fixes, curses, level HP, celestial orbs, special dungeons

Branch: `lemonquake/exciting-albattani-lzv83l`. This file is the working plan **and** the handoff: every phase lists
what is done, where the code lives and how to verify it. If you pick this up from another agent, read
"Status at a glance", then the first phase that is not ✅.

## Status at a glance

| # | Phase | Status |
|---|---|---|
| 0 | Research, tooling, this plan | ✅ done |
| 1 | Evasion investigation + fixes | ⏳ next |
| 2 | +50 HP per level (old and new saves) | ☐ |
| 3 | Level 40+ enemy curse (Hex of Frailty) | ☐ |
| 4 | Celestial orbs: Sora, Luna, Sol, Airah | ☐ |
| 5 | Five special dungeons after Kethrax | ☐ |
| 6 | Tests, screenshots, changelog, push | ☐ |

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
- (fill in as you go)

---

## Phase 2 — +50 HP per level for every hero

- `StatCalculator.LEVEL_UP_HP := 50.0`, added as its own line in Maximum HP: `Level-up bonus (level N): +50 × (N-1)`.
- It is computed from the level every time stats are built, so **old saves get it on load with no migration** and
  new heroes get it as they level. Tempos/guild fighters built by StatCalculator also get it (they mirror heroes).
- Test: an old-format save at level 40 has +1,950 HP over the pre-change formula.

---

## Phase 3 — Level 40+ curses: Hex of Frailty

- New status `hex_frailty` (StatusRules): 5 s, debuff, **-20% all elemental resistances, -15% physical
  resistance, 40% less Evasion**. Cleansable like other curses. Icon: `cursed`.
- New enemy attack kind `"hex"` added at runtime by `Enemy` to every monster of **level ≥ 40** that has a normal
  attack list (not totems/mimics/summons with no damage): a short cast with a purple sigil under the hero; if the
  hero is still in it when it lands, the hex applies. It can be dodged (i-frames) and grazed like any area attack.
  Cooldown 14–18 s; casters/bosses use it more often. Data: `DataEnemies.HEX_ATTACK`.
- Monsters' own `cursed` affix is unchanged.

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
- Icons: rendered in Godot by `tests/tools/render_orb_icons.tscn` → `assets/ui/icons/crystals/<family>_<grade>.png`.

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

## Phase 6 — Wrap-up
- New suite `game/tests/unit/test_bh028.gd`.
- Screenshots in `work/lemondev/bh-028/evidence/`.
- `docs/CHANGELOG.md` (BH-028) and this file's status table.
