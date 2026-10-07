# bh-042 plan — The Abyss: the level-90 climb, ten new bosses, five deep dungeons

Working plan **and** handoff. If you pick this up, read "Status at a glance", then the first phase that is not ✅.
The final user-facing summary goes in `docs/HANDOFF_bh-042.md` when the run ends.

Status: done — see `docs/HANDOFF_bh-042.md` for what shipped, the measured numbers and what changed from this plan
(boss models: OpenGameArt CC0 creatures instead of KayKit/Quaternius, which the user rejected as cartoonish).

## The request (2026-10-07)

1. From level 90 the hero gains less and less experience per kill as they level: a much steeper climb, so dungeon
   farming stops being fast and safe.
2. Every monster of level 90+: **+50 % Defense**, **8× damage**, and health that keeps growing with level ("not afraid
   of a 300-million-HP boss").
3. Sweep and overhaul every dungeon boss from level 90.
4. **Five new dungeons**, level 150–200, reached from a **dungeon room in Malasugue**, each **at least 20 floors**, with
   many layers, climbable stairs and **secret rooms behind destroyable walls**. Darker than usual, few lit torches,
   professionally dressed interiors from **downloaded** 3D assets. Very strong monsters; always very rare drops,
   exceptional on minibosses and bosses.
5. **Ten new bosses (level 90+)** with unique attack patterns (bullet sprays and more). Downloaded models rigged with
   full animations, except the **Fallen Necro-Knight**: built on the game's own hero body, teal-blue pulsing aura,
   always 5 levels above the player, AI that plays like a real player, boss music from the music folder.
6. Every new boss has a **Curse** that stops all spellcasting in an area for several seconds, and an **Armour Rip**
   aimed at one player that removes at least 50 % of their Defense.
7. Added mid-run: **item tooltips with very long descriptions** still do not show properly and consistently,
   especially at **Lape the Ancient**.
8. Screenshots of progress; push to main; build the EXE.

## Status at a glance

| # | Phase | Status |
|---|---|---|
| 0 | Survey, asset sources, this plan | ✅ |
| 1 | Abyss scaling: XP fall-off, +50 % Defense, ×8 damage, health growth (L90+) | ✅ |
| 2 | Boss mechanics: Curse zone (silence area), Armour Rip, bullet patterns | ✅ |
| 3 | Tooltip fix (long descriptions, Lape) | ✅ |
| 4 | Ten bosses: data, attack patterns, Necro-Knight AI + aura + music | ✅ |
| 5 | Downloaded assets: fetch, licence record, convert (textures, props, boss models rigged on the shared skeleton) | ✅ |
| 6 | Five Abyss dungeons: plans (≥20 floors), builder (layers, stairs, secret walls, darkness), loot | ✅ |
| 7 | The dungeon room in Malasugue | ✅ |
| 8 | Overhaul of existing level-90+ dungeon bosses | ✅ |
| 9 | Tests, measurements, screenshots | ✅ |
| 10 | Docs, handoff, protocol bump, push, Windows EXE | ✅ |

Legend: ✅ done · ⏳ in progress · ☐ not started.

## What already exists (do not rebuild)

- **The Descent** (bh-040, `src/core/stats/descent.gd`, `docs/THE_DESCENT.md`): past level 80 monster health and damage
  curves, per-hit limits, resistance penalty, XP requirement ×(1+d/25), kill-XP fall-off past 90, XP lost on a fall.
  bh-042 layers **on top**; nothing below level 85 changes.
- Dungeons: one grid builder (`src/world/maps/dungeon.gd`), storeys 0/1/2, stair flights, seals per floor, raid
  recovery, Usurpers. Plans for big sets are generated offline (`tools/dungeon_gen/gen_plans.py`).
- Boss attacks are data (`DataEnemies*`): kinds melee, projectile, aoe, charge, dash, pools, summon, strikes, beam,
  chain, tongue, tether, gaze, mines, rift … (`Enemy._start_attack`, `EnemyTraitsX.start_special`).
- `silenced` status exists (`StatusRules`); the player and Tempos already refuse spells while silenced.
- `ArenaFighter` (bh-028) is a whole hero on the companion fighting AI (dodge rolls, potions, skills) turned hostile:
  the model for a boss that "plays like a real player".
- Character pipeline (`tools/blender/characters`): a shared skeleton with a 117-clip action library; any mesh skinned
  to it plays every clip. CC0 import precedent: bh-033 (`assets_src/bh033`, `docs/ASSET_SOURCES.md`).

## Phase 1 — Abyss scaling (level 90+)

New `src/core/stats/abyss.gd` (`class_name Abyss`), read by `EnemyStats.build` and `XpCurve.kill_xp`. All constants in
one place; `Abyss.enabled` lets probes measure before/after on one build (like `Descent.enabled`).

| Rule | Value | Notes |
|---|---|---|
| Monster Defense | ×1.5 at level 90+ | eased in over levels 86–90 so there is no wall between 89 and 90 |
| Monster damage | ×8 at level 90+ | same ease-in; multiplies the Descent's damage curve |
| Monster health | ×(1 + ((L−89)/14)^1.25) | ×1.7 at L100, ×6.2 at L141, ×14 at L200, ×33 at L300 |
| Boss health | adaptive health × the same factor, applied after the adaptive clamp | a level-200 Abyss lord lands around 300 M |
| Kill experience past 90 | ×(1 + (L−90)/20)^−1.5 replaces the Descent's ×1/(1+(L−90)/30) | 54 % at L100, 15 % at L141, 6 % at L200 |

Kills per level are recomputed in `test_bh042` and reported in the handoff. The lethal-blow guard (one blow never takes
more than ~35–55 % of the hero's health) stays: ×8 damage makes every hit matter without one-shots from full health.

## Phase 2 — Boss mechanics

- **Curse of Stillness** (attack kind `curse_zone`): a dark teal sigil (telegraphed 1 s) that stays for 5–7 s. Inside
  it every hero and Tempo is `silenced` (no spells; weapon skills still work), refreshed each 0.25 s while they stand
  in it. Readable: a ring, rising motes, the word "Silenced" over whoever it catches.
- **Armour Rip** (attack kind `armor_rip`): a targeted grab/lash at one player (telegraphed line). On a hit it applies
  the new `armor_ripped` status: **−60 % Defense** for 8 s (≥ the requested 50 %), plates fly off, "Armour Ripped!"
  popup. Dodgeable with a roll.
- **Bullet patterns** (attack kind `barrage`, `src/combat/barrage.gd`): `radial` rings, `spiral` streams, aimed `fan`
  waves, `wall` with a gap, `orbit` rings that expand, `cross` rotating arms, `rain` of falling shots, `homing` orbs.
  Lightweight shots (one pooled MultiMesh-free mesh each, distance-checked hits, no physics bodies) so a 60-shot ring
  costs little. Every shot is dodgeable; evasion and dodge i-frames apply.

## Phase 3 — Tooltips (long descriptions, Lape)

Reproduce with `capture_bh041_ui` style capture of an item with every socket + long lore inside Lape's window, then fix
`TooltipLayer` sizing/clipping so long text always shows fully (columns, then a scrolling cap) at both PC and touch
sizes. Regression check over every window that shows an item tooltip.

## Phase 4 — The ten bosses

| # | Boss | Where | Model | Signature patterns |
|---|---|---|---|---|
| 1 | **The Fallen Necro-Knight** | invades any Abyss floor; holds floor 11 of the Throne Beneath | hero body (Persona) in black-and-teal plate, teal pulsing aura | plays like a hero: dodge rolls, potions, combos, Shield Charge, Whirlwind, Death Nova; level = player + 5; boss music |
| 2 | Morvhaal, the Ossuary King | Lord of the Hollow Crown | KayKit Skeleton Warrior (rigged on the shared skeleton) | bone spirals, grave rings, raise the court |
| 3 | The Hollow Archivist | Gatekeeper, Hollow Crown | KayKit Skeleton Mage | page storms (fans), cross beams, curse zones |
| 4 | Ysolde of the Thousand Knives | Gatekeeper, Sunless Cistern | KayKit Skeleton Rogue | knife walls with a gap, blink cuts, armour rip |
| 5 | Thalassor, the Drowned Wyrm | Lord of the Sunless Cistern | Quaternius Dragon (evolved) | tide spirals, rain, homing bile |
| 6 | Kharzul, the Slag Tyrant | Lord of the Ashgrave Foundry | Quaternius Demon | slag radial waves, eruption chases, orbit rings |
| 7 | Gorehelm the Unbowed | Gatekeeper, Ashgrave Foundry | Quaternius Orc (skull) | charge chains, quake walls |
| 8 | Rimehorn, the Last Winter | Lord of the Weeping Bastion | Quaternius Yeti | ice shard fans, freezing spirals |
| 9 | The Weeping Shroud | Gatekeeper, Weeping Bastion | Quaternius Ghost (skull) | orbit wails, homing tears, phasing |
| 10 | The Nameless Sovereign | Lord of the Throne Beneath | KayKit Skeleton Warrior variant, crowned, ×2 scale | every pattern in turn; three phases |

Every one of them has Curse of Stillness and Armour Rip. Downloaded models are put on the shared skeleton (humanoids,
every clip of the action library) or converted with their own clips (creatures, `convert_creature.py`).

## Phase 5 — Downloaded assets (all CC0)

| Source | What | Use |
|---|---|---|
| Kay Lousberg, KayKit Dungeon Remastered 1.0 (GitHub, CC0) | dungeon architecture and props | stairs, arches, gates, banners, candles, chests |
| KayKit Character Pack: Skeletons 1.0 (GitHub, CC0) | four rigged skeletons | bosses 2, 3, 4, 10 |
| Poly Haven (CC0) | castle doors, iron gates, gothic statues, chandeliers, candleholders, fire pit, rocks; castle brick / slate / cobblestone PBR textures | the Abyss look |
| Quaternius Ultimate Monsters (CC0, already in `assets_src/bh033`) | dragon, demon, orc, yeti, ghost | bosses 5–9 |

Provenance (URL, date, size, SHA-256) in `assets_src/bh042/sources.json`; credits in `ASSET_CREDITS.md`.

## Phase 6 — The five Abyss dungeons

| Dungeon | Levels | Floors | Theme |
|---|---|---|---|
| The Vaults of the Hollow Crown | 150–162 | 22 | royal ossuary, cold candlelight |
| The Sunless Cistern | 158–172 | 22 | drowned waterworks, black water |
| The Ashgrave Foundry | 166–182 | 22 | dead forge, ember glow under ash |
| The Weeping Bastion | 174–190 | 22 | frozen fortress, pale blue |
| The Throne Beneath | 186–200 | 22 | obsidian and void, last light |

- Floors 1–10 and 12–21: seal floors; floor 11: the gatekeeper; floor 22: the lord's sanctum. A miniboss holds every
  fifth floor.
- Plans generated by `tools/dungeon_gen/gen_abyss.py`: storeys 0–3 (a fourth layer, 12 m), stair runs between every
  layer, galleries, and 1–3 **secret rooms** per floor sealed by a cracked wall (`#` in the plan). A cracked wall is a
  `Breakable` wall section with health; breaking it opens the room (treasure, sometimes an elite). Dungeon plans keep
  the existing grid language so the shared builder renders them.
- Darkness: ambient light near black, no sun fill, fog; at most 6–8 lit torches/braziers per floor, no floor glow;
  the hero carries a small warm lantern light so the floor is playable.
- Monsters: the Descent + Abyss rules at level 150–200, special-dungeon power ×1.5 health / ×1.3 damage on top.
- Loot: normal monsters drop Legendary+, elites Aether+, minibosses an Ascendant piece (Cosmic+), gatekeepers and lords
  a guaranteed Divine/Eternal/Primordial piece plus their orb and a Relic Cache. Secret-room chests are tier 2.

## Phase 7 — The dungeon room in Malasugue

A new interior, **The Delvers' Undercroft**, under the Sanctuary Terrace (door in `sanctuary.gd`). Five gate arches in a
dim vaulted hall, each with its dungeon's name, level band and the hero's furthest floor; the gate refuses heroes under
level 140. Waypoint-style floor choice works like the existing dungeon gates.

## Phase 8 — Existing level-90+ dungeon bosses

The five Ascendant lords (Seraphel, Morrowgaunt, Zephyrion, Nocthea, Solmara) and every other dungeon boss of level
90+ gain Curse of Stillness, Armour Rip and one bullet pattern suited to them, behind their second phase.

## Phase 9–10 — Verification and release

- `tests/unit/test_bh042.gd`: curves (monotonic, ×8/×1.5 at 90, untouched below 85), XP fall-off, boss health ≈300 M at
  L200, silence zone blocks spells, armour rip ≥50 %, barrage shots hit and miss correctly, all 110 plans parse and are
  connected (every floor reaches its portal; every secret room is reachable only through its wall), loot floors.
- `tests/tools/capture_bh042.tscn`: screenshots of the Undercroft, each dungeon's floors, secret walls before/after,
  each boss and its patterns, the Necro-Knight, the tooltip fix. Evidence in `output/bh-042/`.
- Network protocol 22 → 23 (`net.gd`, `server/service.py`, healthcheck/deploy examples).
- Push to main (evidence and docs, no scratch or raw logs), Windows EXE `build/windows/BeyondHeroes.exe`.

## Decisions taken (and why)

- Ease-in over levels 86–90 rather than a cliff at 90: a level-89 hero entering a level-90 map would otherwise meet
  monsters 8× stronger in one step. At 90 and above the numbers are exactly as requested.
- The Necro-Knight is an `Enemy` boss (so loot, dungeons, the boss bar and multiplayer replication work) with a
  player-like brain, rather than an `ArenaFighter`: arena fighters are local-only and outside the dungeon systems.
- Eschaton stays Lape-only (bh-041 design); Abyss lords give the best drop table below it.
