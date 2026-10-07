# Handoff — bh-042 (2026-10-07): the Abyss

The climb past level 90 is now steep, every monster of level 90+ is far deadlier, ten new bosses, five new 22-floor
dungeons under Malasugue, and the long-tooltip bug at Lape is fixed. **Online version (protocol) 23**: everyone needs
this build, and the official server must be restarted with it. Plan and design: `docs/PLAN_bh-042.md`.

## What you need to do now

1. **Restart the official server** (it runs from this folder): **Stop Official Server.cmd**, then **Start Official
   Server.cmd**. Older games are refused with "Your game is older than this one (online version 23 ...)".
2. **Give your friends the new game**: `build\windows\BeyondHeroes.exe` (917 MB, single file).
3. **Try it**: in Malasugue, walk east of the Sanctuary Terrace stair to the crypt arch (**the Delvers' Undercroft**).
   Inside are five gates. They let in heroes of level 140 and above.

## 1. Level 90 and above (`src/core/stats/abyss.gd`)

| Rule | Value |
|---|---|
| Monster Defense | **x1.5** at level 90+ |
| Monster damage | **x8** at level 90+, on top of the Descent's curve |
| Monster health | x(1 + ((L−89)/14)^1.25) on top of the Descent: x1.7 at L100, x6.2 at L141, x14 at L200, x33 at L300 |
| Boss health | the adaptive boss health (built from the hero's own damage) x the same factor |
| Experience per kill | x(1 + (L−90)/20)^−1.5: 54% at L100, 15% at L141, 10% at L160, 6% at L200 |

How these were applied:

- **Ease-in, not a wall.** Defense and damage ease in over levels 86–90, so a level-89 hero is not hit by a step change. From 90 on they are exactly as you asked.
- **Kills per level** (an ordinary monster of the hero's level): 61 at L90, 150 at L100, 1,173 at L141, 2,140 at L160, 5,558 at L200. Before this change it was 474 at L141.

What the ×8 means in practice, from the bh-040 measurements of your level-141 Archmage:

- A plain monster blow took 2.75% of your health; it now takes about 22%.
- A boss's heaviest critical hit is still capped by the lethal-blow guard (about 35% of your health), so nothing kills you in one hit from full health.
- Expect four or five careless hits to kill you.
- To tune:
  - `Abyss.DAMAGE_MULT` and `DEFENSE_MULT` (damage and defense)
  - `HP_SPAN` / `HP_P` (health growth)
  - `XP_SPAN` / `XP_P` (experience fall-off)

**Boss health is still adaptive.** A hero in ordinary level-200 gear meets a ~18-million-HP Vaelgor; a top-geared hero meets about 14x their old figure (your Archmage's 20.5 M at L200 becomes ~290 M).

## 2. The ten bosses (`src/data/data_enemies_abyss.gd`)

Every one has a **Curse of Stillness** (a teal sigil: nobody inside can cast spells for 6 s; weapon skills still work),
an **Armour Rip** (a lash at one hero: −60% Defense for 8 s; dodge or evade it) and at least two **bullet patterns**
(radial rings, spirals, aimed fans, walls of knives with one gap, curving orbits, homing orbs, rotating crosses —
`src/combat/barrage.gd`). Three phases each.

| Boss | Where | Model |
|---|---|---|
| **The Fallen Necro-Knight** | Gatekeeper of the Throne Beneath; also invades Abyss floors (14% per floor) | Your hero body in black Obsidian Oath regalia, with an Eschaton blade and shield and a pulsing teal aura. Always 5 levels above the strongest hero present. Plays like a hero: dodge rolls (invulnerable), shield blocks against wind-ups, 3-hit combos, three Soul Draughts, and kites and casts when low. Plays `boss_theme`. |
| Morvhaal, the Ossuary King | Lord, Hollow Crown | "Darsh undead creature" (OpenGameArt, CC0) |
| The Flayed Archivist | Gatekeeper, Hollow Crown | "3D horror game monster", black texture set (CC0) |
| Ysolde, the Faceless | Gatekeeper, Sunless Cistern | "Low poly werewolf" — rigged by measured landmarks (CC0) |
| Thalassor, the Drowned Colossus | Lord, Sunless Cistern | "Forest Monster" by Čestmír Dammer (CC0), its tree removed |
| Kharzul, the Slag Tyrant | Lord, Ashgrave Foundry | "Lava golem" (CC0) with a molten-seam shader |
| Gorehelm the Glutton | Gatekeeper, Ashgrave Foundry | "Glutton demon" (CC0) |
| Rimehorn, the Last Winter | Lord, Weeping Bastion | "Giant Mutant" (CC0) |
| The Weeping Shroud | Gatekeeper, Weeping Bastion | "Skull prop" (CC0): a floating six-horned skull |
| Vaelgor, the Nameless Wyrm | Lord, Throne Beneath | "Cethiel's Dragon 3D" (CC0), its own rig and clips |

How the downloaded models got full animations:

- Each model is re-rigged onto **the game's own hero skeleton**, so it plays every one of its 132 clips: slams, sweeps, charges, summons, casts, dodge rolls and deaths.
- The tool is `assets_src/bh042/rig_to_hero.py`. It poses the model's own rig into the hero's T-pose, freezes the mesh there and carries its own skin weights over; the werewolf has no rig, so it gets automatic weights.

Assets I tried and dropped:

- The cartoony Quaternius and KayKit models, after your feedback.
- The free tier of the Fantasy Outfits kit: it only has rangers and peasants.
- A demon statue: its left arm is sculpted into its wing, so it can't be rigged cleanly.

**Older bosses learn the Abyss too.** Every boss met at level 90 or deeper gains a Curse of Stillness, an Armour Rip and a bullet pattern of its own from its second phase. That covers the five Ascendant lords, the Vaults of Zarael and any dungeon boss scaled to a level-90+ hero (`AbyssMoves.overhaul`).

Each Abyss boss carries a dim light of its own, so you can see it in the dark.

## 3. The five Abyss dungeons (`src/data/data_dungeons_abyss.gd`)

| Dungeon | Levels | Gatekeeper (floor 11) | Lord (floor 22) |
|---|---|---|---|
| The Vaults of the Hollow Crown | 150–162 | The Flayed Archivist | Morvhaal |
| The Sunless Cistern | 158–172 | Ysolde | Thalassor |
| The Ashgrave Foundry | 166–182 | Gorehelm | Kharzul |
| The Weeping Bastion | 174–190 | The Weeping Shroud | Rimehorn |
| The Throne Beneath | 186–200 | The Fallen Necro-Knight | Vaelgor |

**Floor layout** (generated and validated by `tools/dungeon_gen/gen_abyss.py`, 110 floors):
- 22 floors each, with layouts up to **four storeys** tall joined by stair flights.
- Seal Keepers guard the way down on most floors.
- A named **warden** (champion) holds floors 5, 10, 15 and 20.
- The gatekeeper (a boss) holds floor 11, the champion floor 21, and the lord's sanctum is floor 22.

**Secret rooms**:
- Every floor hides 1–3 rooms behind a **cracked wall**: masonry with faint glowing seams and grit trickling out.
- Any attack, spell or shot counts. Five blows break it, and it stays broken for that hero.
- Behind it: a tier-2 chest, and sometimes an elite guard.

**Dark**:
- At most 7 lit torches per floor, no fill light, thick dark fog.
- A few deliberate pools of light: a chandelier over the biggest hall, candles on an altar, a fire pit in the foundry.
- The hero carries a small warm lantern on these floors.

**Look**:
- Poly Haven CC0 stone textures, a different pair for each dungeon.
- Poly Haven props: castle doors and iron gates on dead-end walls, gothic statues, lion heads, chandeliers, candleholders, kite shields, maces, busts, mossy rock, fire pits.
- Purposeful room roles from the map-design pass.

**Monsters** come from the existing roster, with the Descent and the Abyss rules at levels 150–200 and x1.5 dungeon health.

**Loot**:
- Ordinary monsters drop a piece 32% of the time, Legendary or better.
- Elites drop three pieces, Aether or better.
- Champions and wardens always add a Cosmic or Divine Ascendant piece.
- Gatekeepers add a Divine or Eternal piece.
- Lords add an Eternal or Primordial piece, plus their orb and a Relic Cache.
- Eschaton stays Lape-only.

## 4. The Delvers' Undercroft

A vaulted hall under Malasugue (`int_delvers`, a safe interior). The entrance is a crypt arch with a Poly Haven castle
door east of the terrace stair. It holds the five gates with their braziers and signs, a chandelier and a lectern.

## 5. Tooltips (the Lape bug)

There were three causes:

1. **Measured too early.** Wrapped text measures its height a frame or two late, so long tooltips were placed by a too-short size and never re-clamped.
2. **Too wide for the screen.** An item and its "equipped" card, each flowed into columns, became a screen-wide panel lying over Lape's window and the slot itself.
3. **A race when hovering quickly.** Moving from slot to slot quickly let an old placement keep working on the new tooltip, splitting it into columns twice.

`TooltipLayer` now:
- waits until the size settles;
- flows into columns only as far as the screen allows;
- sets the equipped card aside (with a line saying so) when both don't fit beside the slot;
- shrinks at most to 80% to stay beside the slot;
- re-clamps whenever it resizes;
- ignores stale placements.

**Measured** with `tests/tools/capture_tooltips_bh042.tscn` (Eschaton/Primordial pieces, 8 sockets, the longest names, in Lape's window and at five screen positions):
- **before: 7 of 30 tooltips unreadable or covering their slot**;
- **after: 0 of 30**.

Shots: `output/bh-042/tooltips/`.

## Tests

- New suite `test_bh042` (11 tests): curves, experience, boss health, Curse/Rip, all ten bosses, the overhaul, every bullet pattern, 110 floors (secret rooms, storeys, wardens), the Undercroft and darkness, loot.
- Updated to the new rules: `test_bh040_descent`, `test_balance_audit`, `test_survival_balance`, `test_bh028` (the Abyss dungeons are "special" too), `test_maps` (the chandeliers' untextured iron), `test_map_design` (room roles for the new themes).
- `test_npcs` counts ten interiors now; the Undercroft is a hall of gates with nobody living in it.
- **Result:** every suite passes except `test_balance`'s 6 long-standing baseline checks, which bh-042 does not change. Details are in `output/bh-042/tests_final.txt`.
- **Slow suites.** `test_maps` (465 s) and `test_map_design` (434 s) now build 110 more floors. The full run therefore stopped after `test_net_guard`, and the remaining 18 suites were run separately with `--only=`.
- **Rechecked.** The suites sensitive to damage and defense were rerun against the final Abyss ramp: 98,006 checks, 0 failures.
- Server: `python -m unittest server.test_service server.test_hardening server.test_control` passes at protocol 23.

## Build

- Windows: `build\windows\BeyondHeroes.exe`, 917,373,008 bytes (bigger than bh-041's 741 MB because of the new models and textures).
  - sha256 `967bb998c42cf4ce1c50269d18b5b1283085b930552fd763fce2f309ae329846`.
  - Built with `--export-release "Windows"`, exit 0; log in `output/bh-042/export_windows.log`.
  - Headless boot smoke: exit 0, no script errors (`output/bh-042/exe_smoke.log`).

## Not done / limits

- **No live bot measurement** of the new damage. The ×8 survivability above is arithmetic on the bh-040 measurements; the Descent probe (`tests/tools/descent_probe.tscn`) can measure it on your save.
- **Bosses as seen in play.** The bosses were screenshot in a lit map and in the dungeons; their attack patterns were fired at an invulnerable hero. Their fights were not played out end to end by a bot.
- **Close-up animation.** Re-rigged models keep their own proportions on the hero's clips, so some poses (hunched brutes swinging two-handed sword clips) look stiff close up.
- **No animations for the Weeping Shroud.** It is a floating skull, by design.
- **No Android build** this time.

## Evidence

Everything is under `output/bh-042/`:

- `shots/`: the Undercroft, floors, secret wall, bosses and fights
- `tooltips/`: before and after
- logs, `tests_final.txt`
- the boss rigging contact sheets: `assets_src/bh042/shots/`
