# The Descent (bh-040): the late game past level 80

Code: `src/core/stats/descent.gd` (every constant below lives there). Tests: `tests/unit/test_bh040_descent.gd`.
Measurements: `tests/tools/descent_probe.tscn`, results in `output/bh-040/`.

Levels 1–80 do not change. From level 81 on, every level makes the world harder than it makes the hero, smoothly, with no
steps. The player sees it as a **Circle of the Descent** every 20 levels (a name only: the numbers never jump).

## 1. What was broken (measured, not guessed)

The player's own level-141 Archmage (a copy of the save, in hidden slot 97) was played by a bot through the real Glasswire
Barrens camps and then against a boss of its level (`descent_probe --mode=live`). The same probe built reference heroes
of every class (class-build points, gear of their level, skills spent like a player, both advancements).

| Level-141 Archmage, before | Measured |
|---|---|
| Normal monsters (51) | **all died to the first hit**, elites too. Biggest hit 18.4 million against 295,000 HP |
| Damage taken clearing the map | **9 HP** (one hit, 0.04% of health) |
| Experience | **+3 levels in 2 minutes: 44 seconds per level** |
| Boss (Astrarch, L144, 3.9M HP) | dead in 27 s; it dealt **5 damage**; it spent 73% of the fight staggered or knocked back |

Nine separate holes, compounding:

1. **Monster damage stopped mattering.** bh-028 tied monster damage to a reference hero of 300 + 40 HP per level. Heroes
   then got 10 attribute points a level, +50 HP a level and much more armour (bh-027, bh-030), but the reference was never
   moved: a plain monster blow took **0.1–0.5% of a hero's health at every level from 20 to 300** (designed: 1–3%).
2. **Only two monsters may swing at once**, at every level (the combat director's tokens never grew).
3. **Experience flattened out.** Kills per level: 42 at L80, 45 at L100, 51 at L141, 58 at L200, 66 at L299. Every map
   gives full experience anywhere, because monsters are always scaled to two levels below the hero.
4. **Archmage keystone had no bound**: "1% more spell damage per 25 Maximum Mana" was ×5.18 at 10,461 Mana. The other
   mage keystone tops out at 40%.
5. **Life leech had no bound**: 4% of one capped 116,000 hit healed 22% of the hero. A few hits a second kept the hero full
   whatever a boss did.
6. **Every hit made a monster flinch**, and a monster could not leave its stagger while a hit reaction played. A hero landing
   several blows a second held bosses helpless.
7. **Pulls and pulses ignored knockback resistance** (Gravity Pull, Aether Pulse): bosses were shoved around 15–22% of a fight.
8. **Adaptive boss health ignored critical hits and keystones**: "25–45 seconds of the hero's damage" was 8–17 s in practice.
9. **Champions and elites had no per-hit limit**: only bosses did (8%), so a 1.5-million-HP champion died to two Meteors.

## 2. How the classics climb (what was borrowed)

| Game | Late-game rule | Here |
|---|---|---|
| Diablo II | Level 90→99 takes as long as 1→90; experience from monsters falls ~2.3% per level past 70; Hell lowers every resistance after the caps; hit recovery only from blows that take a real share of life; death costs experience in Nightmare and Hell | experience requirement and fall-off; resistance penalty; hit recovery; experience lost on a fall |
| Diablo III | Torment tiers multiply monster health and damage; elites gain affixes with depth | smooth health/damage curves; extra elite affixes |
| Path of Exile | Experience penalty past 95; leech rate capped per second; 5–10% experience lost on death in late content | kill-experience fall-off; leech-rate cap; fall penalty |
| Ragnarok Online | Base experience table explodes past 90; levelling becomes a long-term goal | requirement multiplier that keeps growing to 300 |
| Torchlight II | Monster levels track the hero; difficulty adds aggression, not just numbers | more simultaneous attackers, faster attacks, less hesitation |

None of them solves a late game with health numbers alone. Health makes fights longer; danger comes from damage, from
how many enemies act at once, and from how much of the hero's defence still works.

## 3. The system

Depth = level − 80. Monster rules use the monster's level; experience rules use the hero's level.

### Monsters
- **Health** × (1 + 0.022·depth^1.1): ×1.6 at L100, ×3.0 at L141, ×5.2 at L200, ×9.1 at L300.
- **Damage** × (1 + 0.085·depth²/(depth + 10)): eases in (×1.01 at L81), then ×2.1 at L100, ×5.5 at L141, ×10.4 at L200,
  ×18.9 at L300.
- **Resistance penalty** (Diablo II's Hell): a Descent monster's blows strip up to 35% (70 levels deep; 33% at L141) from
  the hero's armour reduction and every resistance, after the 75% caps. Capped heroes lose the most (75% → 40% = 2.4×
  the damage); a hero with no resistance takes 1.35×.
- **Bosses lose their restraint**: bh-028 compressed bosses' heaviest attacks (slope 0.5, ×0.8). Over 60 levels of depth the
  slope returns to 1.0 and the factor to 1.1.
- **The lethal-blow guard loosens**: the most of a hero's health one hit can take rises from 35% (25% for bosses) by 10–20
  points over 120 levels. Still never a one-shot from full health.
- **Nothing falls to one blow**: one hit takes at most 15% of an elite's health and 6% of a champion's (20 levels in), and
  deep down at most 34% of a plain monster's (60 levels in). Bosses keep their 8% limit.
- **Hit recovery** (Diablo II): a blow only makes a monster flinch if it takes 8% of its health (elites 16%, champions 25%);
  bosses never flinch from damage alone. Poise breaks still stagger everyone. A stagger ends after 1.2 s at most.
- **Push resistance**: every push (blows, pulls, pulses, collisions) moves a Descent monster 20% less (elites 50%,
  champions 60%, bosses 80%).
- **They fight harder**: one more monster may swing at once every 25 levels of depth (up to 4 more), attack and skill
  cooldowns up to 1.6× faster, more aggression, less hesitation, more elite packs; elites carry one more affix from L120
  and another from L180.
- **Adaptive bosses** count critical hits and the Archmage keystone in the spell estimate, add half of the weaker damage
  source to the stronger (a rotation weaves weapon blows between spells), all blended in over 60 levels, and are built to
  last 1 + 0.02·depth times as long (×2.2 at L141).

### The hero
- **Leech-rate cap** (Path of Exile): life leech restores at most 6% of Maximum HP per second (phased in over 40 levels).
- **Archmage keystone**: at most 50% more spell damage (reached at 1,250 Mana). The talent text says so.

### Experience
- **Requirement** × (1 + depth/25): ×1.8 at L100, ×3.4 at L141, ×5.8 at L200, ×9.8 at L299.
- **Monsters give less** past level 90: × 1/(1 + (level − 90)/30): 75% at L100, 37% at L141, 21% at L200.
- **A fall costs experience**: 2% of the level's requirement at L81 rising to 10% at L140, taken only from progress inside
  the level (never a level). A friend's revive costs nothing; neither does the Sand Arena.
- Kills per level (normal monster, at level): **42 at L80, 109 at L100, 474 at L141, 1,566 at L200, 5,221 at L299**.

### What the player sees
- The HUD shows **"Descent · Circle IV · The Weeping Deep"** under the hero tier; its tooltip lists every current number.
- Level-ups announce the start of the Descent and each new Circle.
- The experience tooltip shows the requirement multiplier, the monster experience share and the price of a fall.
- The death screen says how much experience a respawn will cost.
- The Field Guide (Dungeons & Relics page) explains the Descent and shows the hero's own numbers.

Circles: I The Threshold (81), II The Ashen Stair (101), III The Ember Halls (121), IV The Weeping Deep (141), V The Iron
Gaol (161), VI The Bone Orchard (181), VII The Drowned Choir (201), VIII The Starless Vault (221), IX The Broken Throne
(241), X The Last Furnace (261), XI The Bottom of the World (281).

## 4. Results

Bot runs on the real game (Glasswire Barrens, every camp, then an Astrarch of the hero's level). The bot stands still at
range and never dodges, so survival numbers are worst cases. Evidence: `output/bh-040/measurements/{before,tuning,final}`.

| Hero (L141 unless noted) | Normal TTK | Elite TTK | Min per level | Boss | Lowest HP |
|---|---|---|---|---|---|
| **before** — the player's Archmage | one hit | one hit | 0.7 | 3.9M in 27 s | 100% (took 5 HP) |
| **before** — Master-geared Mage | 13.6 s | 33.7 s | 3.5 | 1.5M in 74 s | 91% |
| the player's Archmage | 1.6 s | 5.3 s | 7.7 | 12.1M in 90 s | 86–97% |
| the player's Archmage, same gear at L160 | 2.5 s | 10.9 s | 15 | 14.7M in 86 s | 88% |
| the player's Archmage, same gear at L200 | 4.2 s | 17.0 s | 39 | 20.5M in 102 s | 45% |
| Legendary-geared Mage, L100 | 11.6 s | 38.1 s | 8.6 | 1.2M in 105 s | 91% |
| Primordial-geared Mage | 9.2 s | 40.4 s | 34 | 9.4M in 185 s | 20% |
| Master-geared Mage | 28.7 s | 36.2 s | 119 | 5.4M in 213 s | 7% |

Blows on the player's Archmage at L141 (average roll, before evasion), before → after: plain monster hit 0.23% → 2.75%;
elite champion's heaviest critical 0.88% → 10.7%; boss plain 0.5% → 8.8%; boss heaviest critical 1.5% → 31.5% (the
loosened guard allows 34.8% from a level-141 boss).

Limits of the measurement: the melee bot (Knight, Shadowblade) often stalls on bosses, so their boss times are not
reliable; Mage and Ranger runs are. A boss picks its attacks at random: the Archmage's biggest boss hit ranged 1–12%
across four runs. Levels 20–80 are untouched and remain soft (a plain blow takes 1.6–3% of an Advanced-geared hero, much
less of a well-geared one); restoring the bh-028 design there is a separate change.

Tests: `test_bh040_descent` (16 tests, 2,469 checks) passes; the full suite passes except `test_balance`'s known
level 1–30 class band (6 of 16, as before). `test_bh028_arena`, `test_balance_audit`, `test_survival_balance` and
`test_transcendence_net` were moved to the new contract.

## 5. Where to tune

Everything is in `descent.gd`. `test_bh040_descent` pins the shape (smooth, monotonic, untouched to 80) rather than the
exact numbers, so tuning a constant should not break it.

- Monsters too tanky / too soft: `HP_A`, `HP_P`.
- Monsters hit too hard / too soft: `DMG_A` (all heroes), `RES_PENALTY_MAX` (mostly heroes at the caps).
- Levelling too slow / too fast: `XP_REQ_SPAN` (requirement), `XP_KILL_SPAN` (monster experience past 90).
- Deaths too punishing: `DEATH_XP_MIN`, `DEATH_XP_MAX`.
- Strong builds overkill too easily: `NORMAL_HIT_SHARE`, `ELITE_HIT_SHARE`, `CHAMPION_HIT_SHARE`.
- Too swarmy: `TOKEN_EVERY`, `TOKENS_MAX`, `SKILL_RATE_MAX`.

Measure before and after on one build: `descent_probe --descent=off` switches the whole Descent (and the Archmage bound)
off for that run only.

## 6. Multiplayer

Every monster rule is a function of the monster's level, so host and guests agree. Network protocol 20 → 21 (net.gd,
server/service.py, server/healthcheck.py) so a Descent host never shares a world with an older client.
