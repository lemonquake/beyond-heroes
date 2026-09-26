# Beyond Heroes — Handoff for run bh-004 (Malasugue interiors + Tempo companions)

**Read this first, then `docs/NEXT_STEPS.txt` (the bh-003 plan this run was executing), `docs/LORE.md` (lore bible)
and `work/lemondev/bh-003/contract.md` (invariants).**

Status in one line: **§2 below is done** (see §3 at the end): suite green on 4.7.2 (4717 checks, 0 failures) with new
`test_npcs`, `test_tempos`, `test_chat`; town, interiors and Tempo UI rendered and reviewed; the combat bot runs the Tempo
AI without errors. Invented Filipino-derived names were replaced (§3.1). Nothing is committed yet (ask first).

---

## 0. Environment facts (important — they changed since bh-003)

- **The user runs Godot 4.7.2**, not 4.4.1: `C:\Users\Lemon PC\Desktop\Godot.exe` (Git Bash path
  `"/c/Users/Lemon PC/Desktop/Godot.exe"`). `game/project.godot` has `config/features=("4.7", ...)` and the
  `.glb.import` files were re-imported by 4.7 (that is why ~100 `*.import` files show as modified — leave them).
- With 4.4.1 (`tools/run_tests.sh` default) `test_enemies` now fails 234 checks because the import cache is 4.7's.
  **Always test with 4.7.2:**
  ```bash
  cd game && G="/c/Users/Lemon PC/Desktop/Godot.exe"
  "$G" --headless --path . --import            # refresh class cache after adding class_name scripts
  "$G" --headless --path . res://tests/run_tests.tscn 2>&1 | grep -E "^\[(PASS|FAIL)\]|^  FAIL|TOTAL|SCRIPT ERROR"
  "$G" --headless --path . -s res://tests/tools/compile_all.gd | grep -E "COMPILE|FAILED"
  ```
  Baseline before this run: 3578 checks, 0 failures (on 4.7.2). Last full run in this run: 3839 checks, 3 failures —
  all three were expected and **the test file has been updated since** (see §3); re-run to confirm 0.
- `-s` SceneTree scripts cannot use autoload identifiers (`Game`, `DB`...). For ad-hoc probes use
  `game/tests/tools/_probe.tscn` + `_probe.gd` (a Node scene; edit `_probe.gd` and run it). **Delete both `_probe.*`
  files before committing.** `work/probe/` holds scratch output (screenshots, logs) — do not commit it.
- Physics engine is **Jolt**. The machine has a real GPU, so rendered captures work: run without `--headless`, e.g.
  `"$G" --path . --resolution 1600x900 res://tests/tools/capture_maps.tscn -- --maps=sanctuary --out=../work/probe`.
- The shell tool mangles heredocs containing quotes; write Python patch scripts to the scratchpad with a file-write
  tool and run them.
- Branch: user is on `main` (= `update-0.01-q1u5d0` + one import-cache commit). NEXT_STEPS says commit/push to
  `update-0.01-q1u5d0`; **ask the user before committing/pushing** (they have not asked yet).

---

## 1. What was done (uncommitted)

### 1.1 Floating NPC bug — root cause found and fixed
- The bh-003 hypothesis (ray before the first physics step) was **wrong**: with Jolt the ray hits in the same frame.
- Real cause (reproduced): `Game.load_map` only `queue_free`d the old map, so its colliders were still in the physics
  space while the new map was populated. Returning from the Ruined Forest put Tovin 6 m, Brannoc 4.6 m, Seris 3 m in
  the air (the ray hit the forest terrain). Doors would have made it worse.
- Fixes: `game.gd` removes the old map from the tree before adding the new one; `NpcDirectory.ground_height` ignores
  colliders that are not descendants of the map (loops with ray exclusions) and starts 6 m above the point (under
  roofs/stall canopies); `Npc._settle()` re-snaps once after the first physics frame.
- **Still to do:** the regression test (see §2.1).

### 1.2 NEXT_STEPS §3.1 — buildings placed in Malasugue (`world/maps/sanctuary.gd`)
- Five `house_intact_door` lots (`HOUSE_LOTS`) and three halls (`HALLS`): Salted Marlin `(-28.8, 13.5)` yaw 90,
  Swordfin Hall `(32, -4.8)` yaw -90, Lantern House `(-30, -9.5)` yaw 90. The NW house moved from `(-22,-16)` to
  `(-21,-19)` yaw 55 because the Lantern House overlapped it (checked with an oriented-box overlap script).
- `door()` helper puts a `DoorPortal` at each building's `door` socket and a `door_<interior_id>` spawn 1.6 m out.
  Note: the real house door socket is `(0,0,4.0)`, not the `(0,0,3.4)` NEXT_STEPS quoted (that was `door_light`).
- Lights at `door_light` / `sign_light` / `lantern_light` / banner sockets; trees at (-31,-4), (31,-6), (-30,18)
  removed (two replacements added elsewhere); greenery avoids oriented `FOOTPRINTS`; `_splat` paths lead to doors.
- New **Shrine of the Fallen** at `SHRINE = (13.5, 0, -11)` (east of the terrace stair) for the Tempo-Caller.
- New views: `tavern`, `guild_halls`, `shrine`, `topdown`.
- Town renamed **"Malasugue Town"** in `data_maps.gd` (id stays `sanctuary`); "Hero Sanctuary" wording replaced in
  items, objectives, loading screen, menu comment, teleporter labels and NPC dialogue ("Sanctuary Terrace" kept).

### 1.3 NEXT_STEPS §3.2 — eight interiors (`world/maps/interior.gd`, `data_maps.gd::interiors()`)
- One builder, `compose()` switches on id: `int_tavern`, `int_swordfin`, `int_lantern` (stone floor), and the homes
  `int_netmender`, `int_cartographer`, `int_widow`, `int_keeper`, `int_refugee`. Layouts per NEXT_STEPS table.
- `_room()` builds plank floor at y=-0.1 (+ `walk_slab`), walls with fronts facing the room (explicit yaws — note
  `MapBuilder.room()` faces east/west walls outward, so it was not used), low south wall with a 4 m exit gap, porch
  slab + invisible boundaries, exit `DoorPortal` back to `sanctuary/door_<id>`, `start` spawn, bounds, views
  `room`/`overview`/`entrance`, dim warm environment, 2–4 flickering lights.
- **Not verified in-game or rendered yet** (furniture overlap/orientation, wall facing, lights, navmesh).

### 1.4 NEXT_STEPS §3.3 — NPC roster (`data/data_npcs_town.gd`, registered in `database.gd`)
- 13 LORE §6 people with lore-rooted graphs: Hesta (rest service + flag-driven rumours), Fennick, Old Marrow, Venna,
  Commander Rhea, Dax (registrar), Archivist Oren, Lio (registrar), Tessaly, Aurand, Ilvena, Keeper Thadric, Zerin.
  Registrars share `_registrar_graph()` (join / transfer / promote / tier explanation / perks / bounties).
- Plus **Veyra Ashgrave, the Tempo-Caller** (town, at the shrine; `elder.glb`; portrait `tempo_caller.svg`).
- Maelis → `elder.glb`, Tovin → `merchant.glb`, Brannoc → `smith.glb`; Seris now charges (`mystic_heal`,
  "{mystic_fee} gold") and points to the Salted Marlin.
- `Npc` fidget personality falls back to `townsfolk` (idle_look/idle_adjust) for non-hero models.
- Dialogue additions: placeholder `{promo_deed_text}`, conditions `tempo_fallen`, `tempos_min`, services
  `tempo_hire`, `tempo_revive`; `DialogueBox.SERVICES` lists every valid service (for tests).
- LORE.md §6 table **not yet updated** with Veyra Ashgrave (see §2.5).

### 1.5 NEXT_STEPS §3.4 — new enemies in the Ruined Forest (`ruined_forest.gd::_raiders()`)
- Goblin camp `(-26,0,-18)` (5 skulkers), orc scouts `(21,0,28)` (2 reavers + goblin), chained ogre `(40,0,25)`,
  two dire-wolf dens `(-14,0,-30)`, `(42,0,-26)` (3 each); tree scatter keeps these clearings open.
- **Not checked** that the zones are reachable on the navmesh or that the levels feel fair.

### 1.6 NEW: the Tempo companion system (user request)
Spirits of warriors who died fighting monsters, bound by Veyra Ashgrave. Files:

| File | Role |
|---|---|
| `src/data/data_tempos.gd` | classes (Swordsman/Archer/Thief), 12 skills (4 per class, one heal each), 5 personality traits, 18 death origins, **100 names**, constants (`MAX_ACTIVE=2`, `MIRROR=0.5`, roster size/refresh) |
| `src/core/tempos/tempo_data.gd` | persistent model (uid, name, class, trait, skills, origin, tint, price, own `Equipment`, fallen, hp/mana fractions, kills) |
| `src/core/tempos/tempo_rules.gd` | stats mirror, gear gating, equip/unequip, roster generation, hire/revive/release costs & rules, `restore_all` |
| `src/actors/tempo/tempo.gd` | the Actor + AI (see below) |
| `src/actors/tempo/tempo_bar.gd` | floating HP+mana bar |
| `src/actors/tempo/tempo_party.gd` | spawn on map load, sync HP/mana to data, refresh after hire/release, regroup |
| `src/ui/windows/tempo_window.gd` | **O key**: tabs per Tempo, 3D preview, 13 gear slots, live HP/mana, stats, skills, hero bag (right-click/drag to equip), Release |
| `src/ui/windows/tempo_caller_window.gd` | Veyra's shrine: roster cards (bind), your Tempos (call back / release) |
| `src/ui/hud/tempo_frames.gd` | always-on HUD party frames (HP + mana, state, fallen) under the portrait |
| `tools/ui_art/bh004_tempos.py` | generated 12 skill icons, 3 class crests, the Tempo-Caller portrait (already written to `game/assets/ui/...`) |

Rules as implemented:
- **Stats**: 50% of the hero's persistent stats (`hero.compute_stats([])`) fed as FLAT modifiers for pools, defense,
  evasion, accuracy, crit, damage bonuses, resistances, added damage; then the Tempo's own gear, class and trait mods
  (INC/MORE apply to the total). Move speed never below 1.05× the hero's. Empty hands → a "ghost blade" loadout that
  scales with level.
- **Gear**: max rarity = one below the best the hero may wear (`TempoRules.rarity_cap`; Unranked hero → Advanced,
  E → Licensed, D → Elite, C → Master, B → Mythical, A+ → Legendary); class weapon lists; hero level requirement;
  attribute requirements ignored.
- **Party**: max 2 bound (fallen count until called back or released). Hired Tempos arrive with a Beginner class
  weapon. Revive fee `25 + 12·level + 20% of price`. Resting at the inn restores Tempos.
- **AI** (`tempo.gd`, think 0.15 s, danger scan 0.08 s): dodge-roll with i-frames or walk out of telegraphed blasts
  (`AreaEffects` nodes now join groups `telegraph`/`hazard`/`sweep`), boss/elite wind-ups, charges, projectiles;
  heal hero first (earlier when critical), then the other Tempo, then self; retreat below the trait threshold and
  rest-regenerate; target scoring (who hits the hero, casters, wounded, bosses, hysteresis, leash 20 m); class roles
  (swordsman body-blocks + taunt, archer kites with LOS, thief flanks/backstabs); follow in formation, teleport back
  when >30 m or stuck. `decided(what)` signal + `debug_log` for testing.
- **Enemies** (`enemy.gd`): `target` is now `Actor`; threat table (damage from hero/Tempos, decaying), hero bias,
  stickiness, `taunt(by, t)`, `lose_target(who)` (smoke), `_target_winding_up()`. `Actor` gained virtual
  `in_combat()` and `current_action()`.
- **FX**: Tempo hits don't hitstop/shake the camera; Tempo damage numbers tinted; spirits "bleed" light (`Gore.AETHER`).
- **Save**: `HeroData.tempos`, `tempo_roster`, `tempo_serial` (older saves load with none; roster normalised through
  `TempoData` for exact JSON round trips). `SaveSystem.CURRENT_VERSION` was **not** bumped (new keys are optional).
- Hooks: `Game.load_map` (sync before unload, `TempoParty.spawn_for` after NPCs), `save_now` (sync),
  `place_player` (regroup); Events `tempo_changed`, `tempo_fallen`, `tempo_spawned`; input action `tempos` = O
  (also in Settings rebind list); minimap shows Tempos as cyan dots.
- `tests/tools/combat_bot.gd` gained `--tempos=archer+heal,swordsman` (binds Tempos, records hits/kills/decisions/
  heals). **It has never been run** — the user interrupted right before the first run.

---

## 2. What to do next (in order)

### 2.1 Tests (headless, 4.7.2)
1. Re-run the suite; expect 0 failures (the two NPC-count checks in `test_shops_dialogue.gd` were updated to 6/7 and
   the portrait now exists).
2. New `tests/unit/test_npcs.gd` (strict): **float regression** — real `Player`, `Game.load_map(ruined_forest)` then
   `load_map(sanctuary, waypoint)`, wait 2 physics frames, every NPC `|y − ground ray| < 0.1`; same for each interior
   (via its `start`). Data: every NPC's map exists; every `service` value ∈ `DialogueBox.SERVICES`; every graph target
   resolves (existing `test_data_is_consistent` already covers new NPCs).
3. **Door cycle test**: for each of the 8 interiors: from sanctuary `door_<id>` → interior `start` → back; player on the
   right spawn; interior has its NPCs; its exit portal targets `sanctuary/door_<id>` which exists; after 3 cycles
   exactly one map under `world_parent`, one player, no duplicate NPCs/Tempos. Every sanctuary DoorPortal's target map
   exists and every interior has `start`.
4. New `tests/unit/test_tempos.gd`: 100 unique names, classes/skills/traits consistent; mirror (thief with no gear:
   `max_hp == floor(0.5 × hero max_hp)` ±1) and growth on level-up; gear gating per tier (Unranked/E/D) and class
   weapons; equip/unequip/release move items exactly; hire cost exact, 3rd hire refused, roster deterministic and
   refreshes; revive cost/state; save JSON round trip exact; AI in a live map (sanctuary + `Spawner.spawn_enemy`):
   heal fires on a hero at 30% HP, dodge out of an `AreaEffects.delayed` blast placed on the Tempo, retreat at low HP,
   enemy retargets to a Tempo that out-damages the hero, taunt forces target, follow + teleport when far.
5. Run the combat bot:
   `"$G" --headless --path . res://tests/tools/combat_bot.tscn -- --class=knight --maps=ruined_forest --seconds=90 --tempos=archer+heal,swordsman --out=../work/probe`
   and read `work/probe/combat_knight.json` + grep the log for `SCRIPT ERROR`. Expect runtime errors on first run —
   the Tempo AI has only been compiled, never executed. Likely spots: dictionary field access in `_scan_danger`
   (`en._charge`, telegraph/hazard/sweep members), `_try_skill` casts `(target as Enemy)`, skills' `sk.anim` on a
   duplicated dict, `TempoParty.spawn_one` ground placement, `TempoWindow`/`TempoFrames` layout.

### 2.2 Visual verification (real renderer, not headless)
- Town top-down (`view topdown`) and `tavern`/`guild_halls`/`shrine` views: no overlaps, door portals at the doors,
  paths, lights, no grass through buildings. NPCs on the ground after forest→town travel.
- Each interior's `room` view (add a `capture_interiors` tool per NEXT_STEPS §3.5, or use `capture_maps.tscn --maps=int_tavern,...`).
  Check wall facing (window sills/door leaf toward the room), furniture against walls not intersecting, rugs visible.
- Tempos in the forest with the game camera: spirit look (rim, 0.84 dithered opacity, wisps, light), weapons in hands,
  name plate/bar height, HUD frames position (`hud.gd`, `Vector2(24,150)`) not overlapping buffs, Tempo window and
  Shrine window layout at 1920×1080.
- `capture_enemies` re-run from NEXT_STEPS §3.5 (still pending from bh-003).

### 2.3 Balance / feel (after it runs)
Hire prices (80+30/level), revive fee, rest regen (4.5%/s), retreat thresholds, dodge cooldowns, ghost-blade damage,
enemy `HERO_BIAS`/threat decay; confirm Tempos don't steal all aggro and don't pull idle packs (they engage idle
monsters only within 11 m of the hero while the hero fights).

### 2.4 Known gaps / risks
- `SaveSystem.CURRENT_VERSION` still 3; consider a v4 bump + migration test if the contract requires it.
- Player death: Tempos keep fighting until the respawn reload; fallen Tempos stay fallen (by design) — verify the
  respawn reload doesn't duplicate them.
- `TempoWindow` bag grid is fixed at 60 cells (`Inventory.COLUMNS*ROWS`); Inventory capacity changes would break it.
- `Npc` positions in interiors assume room-centred coordinates; verify `NpcDirectory` ground rays hit the planks.
- NEXT_STEPS §3.6 builder issues (sentinel grip, archer arrow, stalker rim, weapon bones, `anim_meta.json` regen)
  untouched — needs bpy/Blender, low priority.
- Minor: 4.7 prints `AnimationNodeBlendSpace2D::add_blend_point: No name provided` warnings from
  `character_visual.gd::_bs` — pass a name to silence them (API exists in 4.7; keep 4.4-compatible if still required).

### 2.5 Docs
- `docs/LORE.md`: add Veyra Ashgrave to §6 and a new **§9 Tempos** (who they are, the Shrine of the Fallen, half-strength
  bond, one-tier-lower gear, two at a time, classes, calling back the fallen — all *provisional*). Mark Tempos as
  provisional author-requested canon.
- Update `docs/NEXT_STEPS.txt` (or replace with this file) once §2 is done.

### 2.6 Definition of done (bh-003 DoD + Tempos)
- No floating/sunk NPCs (test + render); 8 interiors enterable/exitable, door-cycle test clean; 13+1 NPCs with dialogue;
  guild join/promotion and the inn reachable in play.
- Tempos: hire, equip (O window), fight, heal, dodge, retreat, fall, revive, release, save/load — each covered by a
  test and seen working in a rendered playtest.
- Suite green on 4.7.2; `_probe.*` and `work/probe/` removed; changes committed (and pushed only if the user agrees).

---

## 3. Continuation (same run, second session)

### 3.1 Names — no Filipino names or words (user instruction, permanent)
The user never asked for a Filipino setting. Every invented Filipino-derived name was replaced with an original one
(LORE §8 now forbids borrowing names/words/folklore from real cultures). "Jre", "Salmonan" and "Malasugue" are the
author's own names and were kept.

| Old | New | | Old | New |
|---|---|---|---|---|
| Pilar Abucay (innkeeper) | **Hesta Brindle** (`hesta`) | | Bangusan (north island) | **Veldmoor** |
| Ciro Balintad (bard) | **Fennick Arlow** (`fennick`) | | Lakanmar (Registry city) | **Aubren** |
| Old Tasyo (fisherman) | **Old Marrow** (`marrow`) | | Tulingan (east island) | **Corvessa** |
| Nena Lagdameo (net-mender) | **Tessaly Grane** (`tessaly`) | | Tambakol (south island) | **Emberhal** |
| Ibarra Quell (cartographer) | **Aurand Quell** (`aurand`) | | Aurelio (garrison bowman) | **Edrin** |
| Mirasol Hald (widow) | **Ilvena Hald** (`ilvena`) | | Dax Mercado | **Dax Harrowby** |
| Keeper Tomas Dalisay | **Keeper Thadric Moll** (`thadric`) | | Lola Amihan (Tempo-Caller) | **Veyra Ashgrave** (`veyra`) |
| Yusra Ven (refugee) | **Zerin Ven** (`zerin`) | | 100 Tempo names | 100 new invented names (`DataTempos.NAMES`) |

Also: "malasugue" is no longer used as a fish word in dialogue; the fisher's conical "salakot" hat became an oilskin
**sou'wester** (model rebuilt with Blender 5.2 via `build.py -- fisher`, portrait `fisher.svg` regenerated from
`bh003_portraits.py`).

### 3.2 Chat box and cheat codes (user request)
- **Enter** (input action `chat`, rebindable, also keypad Enter) opens a text line bottom-left (`src/ui/hud/chat_box.gd`,
  owned by `UIRoot`, drawn under the windows). Enter sends, Esc or an empty line closes; gameplay input is blocked while
  typing. Messages show as `[Hero] text`; the log keeps 8 lines and fades 8 s after the line closes.
- Cheat codes (`src/core/cheats.gd`, whole message, any case): **`lemonq`** +5000 gold · **`azrin`** +3 levels (points
  included, stops at the level cap) · **`azrael`** full HP and mana (hero and living Tempos). Codes are not echoed.

### 3.3 Done from §2
- Tests: `test_npcs.gd` (NPC data, float regression forest→town→every interior→town, 3× door cycles over all 8 interiors
  with 2 Tempos: right spawns, residents, exits, one map / one player / no duplicate NPCs or Tempos), `test_tempos.gd`
  (names/classes/skills/traits, 50% mirror and growth, gear gating Unranked/E/D + class weapons, equip/unequip/release,
  hire cost/3rd refused/roster determinism and refresh, revive, save JSON round trip + legacy save, live AI: heals the
  hero at 25%, dodge-rolls a 0.45 s telegraphed blast, retreats when hurt, enemies switch to a Tempo that out-damages the
  hero, taunt, follow + rejoin at 45 m, both Tempo windows open), `test_chat.gd`.
- **Bug fixed:** opening the Tempo window (O) with a bound Tempo recursed forever and crashed (tab rebuild emitted
  `tab_changed` → `refresh()`); `tempo_window.gd` now blocks the tab bar's signals while rebuilding. Regression-tested.
- Combat bot (`--tempos=archer+heal,swordsman`, 90 s, ruined forest): no script errors; Tempos 74 hits, 12 of 15 kills,
  9 dodges, pierce/volley/cleave used. (The knight bot itself was stuck ~64 s, so the kill split says little about balance.)
- Renders reviewed (`capture_maps` town + 8 interiors; `capture_ui --tempos=1` added: chat, Tempo window, Tempo-Caller
  window, Tempos in the forest). No overlaps, walls face inward, doors lit, spirit look/plates/HUD frames fine.
- LORE: Veyra Ashgrave + Shrine of the Fallen in §6, new §9 Tempos (provisional), naming rule in §8.
- `_probe.*` deleted.

### 3.4 Still open
- Balance pass (§2.3) in real play; Tempos may take too many kills — watch `HERO_BIAS` / threat decay.
- `SaveSystem.CURRENT_VERSION` still 3 (new keys are optional; legacy load is tested).
- The `add_blend_point` "no name" warnings were left alone: passing a name breaks 4.4 (see commit 51706c7).
- NEXT_STEPS §3.6 builder issues (sentinel grip, archer arrow, stalker rim, weapon bones) untouched.
- Commit/push: not done — ask the user (`work/probe/` must not be committed).
