# Combat scaling (bh-028)

This is how hero, monster and boss numbers are tied together from level 1 to 300. The code is in
`src/core/stats/combat_budget.gd`. Before bh-028 the three kinds of numbers each grew on their own curve. Nothing kept
them in step, so the game was easy for some builds at some levels and lethal for others. This document explains what
went wrong and what replaced it.

## What was broken

The probe in `tests/unit/test_bh028.gd` (and the earlier measurement run) put real geared heroes against every monster
in the game. It measured the share of the hero's health that one blow takes.

- **Monster damage was sized for one kind of build.** Strength gives 6 HP per point and Wisdom 4 HP per point. A hero
  who spends points along their class's build has about 2,000 HP at level 50. A mage who puts every point into
  Intelligence, or a ranger who puts every point into Dexterity, has about 750. Monster damage did not know the
  difference.
- **Multipliers stacked with no ceiling.** The largest single blow was the product of:
  - the attack's multiplier (up to 4.2)
  - elite (1.3), champion (1.25) and difficulty (Mythic 1.4)
  - a critical (1.5)
  - Shocked or Cursed, which add damage taken

  On a level-50 mage who put every point into Intelligence, on Mythic, an elite champion's heavy critical took
  **94% of their health**. One more hit from anything was death. With a status ailment on top, that blow alone killed.
- **Enemy levels jumped.** From level 30, monsters were floored in 15-level steps: 30, 45, 60 and so on. On the hero's
  45th level, every monster jumped 15 levels at once. That added +27% damage, +60% health and another +4% milestone
  bonus. This was the "level 40-45 wall".

## The new model

### 1. The reference hero

`CombatBudget.hero_hp_ref(L) = 300 + 40 × (L − 1)` is the health of an average hero of level L. The 40 per level is made
of:

- the four classes' average health per level (about 9)
- three of the ten stat points per level going to Strength or Wisdom (about 15)
- gear growth (about 16)

Check it against measured heroes in `test_bh028`.

### 2. Monster damage follows the reference hero

For levels 1-5, monster damage keeps the authored per-level growth. After level 5, the damage multiplier is

    damage_scale(L) = damage_scale(5) × hero_hp_ref(L) / hero_hp_ref(5)

so a monster blow takes **the same share of an average hero's health at level 10, 50 or 300**. The milestone damage
bonus is gone. Monster health on top of `health_factor` is one smooth curve now. It passes through the old checkpoint
values, but it has no steps.

### 3. Encounters stay close to the hero

From level 30, monsters spawn at most `ENCOUNTER_GAP` (2) levels below the hero. They used to be floored in 15-level
steps. A level-44 hero now meets level-42 monsters rather than level-30 ones. On the 45th level nothing jumps. Bosses
still match the hero exactly.

### 4. Vitality

Every hero gains **16 HP per level after level 5**, whatever their build. The character sheet shows it as a line of
Maximum HP. Monster damage does **not** follow Vitality. That is deliberate: Vitality is the safety margin, and it
matters most to builds with no Strength or Wisdom. The level-50 mage who puts every point into Intelligence now has
about 1,470 HP, up from 749.

### 5. Ranks and bosses

| rank | damage | lethal-blow guard |
|---|---|---|
| normal | authored | 35% of max HP |
| elite | ×1.3 | 35% |
| champion | ×1.3 elite × champion bonus | 35% |
| boss | ×0.8; attack multipliers above 1.6 count at half rate (a 4.2× slam hits like 2.9×) | 25% |
| another hero (Sand Arena) | ×`pvp_mult(level)` | 20% |

A boss can still have an enormous health pool (`EnemyStats.boss_health`), so a boss fight stays long. Its heaviest
critical, on a hero with average gear, now takes **at most about 20% of their health. That is five hits.**

### 6. The lethal-blow guard

`Actor._threat_guard` caps every hit on a hero or a companion at the attacker's rank share of the target's maximum HP.
The cap is applied last, in `DamagePipeline`, after every bonus, critical, vulnerability and defence. It is a floor for
heroes who are under-geared or built as glass cannons; heroes with average gear stay well below it. Monsters
themselves have no guard. Damage over time is not capped, because each tick is already small.

## What it looks like (Veteran, gear of the hero's level, points along the class build)

The share of maximum health that one blow takes:

| | plain monster blow | elite champion heavy crit | boss heaviest crit |
|---|---|---|---|
| Knight (Advanced gear), L10 → L300 | 1.0-1.3% | 10-13% | 4.6-5.8% |
| Mage (Advanced gear), L10 → L300 | 2.2-2.9% | 22-29% | 14-18% |
| Ranger (Advanced gear), L10 → L300 | 2.3-3.2% | 23-33% | 15-20% |
| Shadowblade (Advanced gear), L10 → L300 | 2.2-3.3% | 22-33% | 14-20% |

These numbers barely move between levels 30 and 300. That flatness is the point. Before bh-028 the same table had
spikes at 30 and 45. It also drifted by class and build, and on Mythic an elite's blow took 94% of a glass mage's
health.

## Hero against hero

Heroes are tuned to kill monsters that have many times a hero's health. Hero offense also compounds faster than any
health curve: attributes add physical attack quadratically, weapons grow with the weapon budget, and increases stack.
So damage between heroes cannot be a fixed fraction. Every blow from a hero on another hero, or on an arena adventurer,
is multiplied by

    pvp_mult(L) = PVP_HIT_SHARE × hero_hp_ref(L) / ref_hit(L)

`ref_hit(L)` is the plain weapon hit of the **reference hero** of the attacker's level. That hero is a Knight whose
points follow the class build, wielding the best ordinary sword of that level at Advanced rarity. The value is
measured once per level with the real stat code and kept. A reference hit therefore takes 7% of a reference hero's
health before armour. A better weapon, skills and criticals keep their edge, because they are measured against the
same yardstick. No single blow between heroes takes more than 20% of the target's health.

Measured basic-attack duels, Advanced gear, armour included (`test_bh028.test_pvp_duel_length`):

| level | Knight → Mage | Ranger → Shadowblade |
|---|---|---|
| 10 | 9.7 s | 9.9 s |
| 30 | 10.3 s | 12.1 s |
| 50 | 10.9 s | 9.7 s |
| 100 | 11.8 s | 8.3 s |
| 300 | 10.3 s | 6.4 s |

Before the reference hit, the same duels lasted 12 s at level 50 and under 2 s at level 300. A Ranger's duels end
sooner at high level because crossbow hits grow with Dexterity. That is a property of the build, not of the scaling.

## The Sand Arena (Wyman Outpost)

This is the free-for-all ground where the hero-against-hero rules apply (`world/arena_grounds.gd`). The arena is a
ring of sand, 40 m across, inside a palisade south of the Fen Road. A lane leads to its gate. Spectator galleries
stand on its east and west sides, and adventurers walk in through a barred door opposite the gate.

- **Who fights.** Every hero on the sand fights every other hero there:
  - players against players
  - players against adventurers
  - adventurers against everyone

  Another player's hero is a target only while both heroes stand on the sand (`NetAvatar.set_arena_hostile`).
- **Adventurers.** There are six adventurers (`actors/tempo/arena_fighter.gd`). Each is a whole hero with a random
  class, a name, a look, gear of their level (Advanced to Master) and two or three draughts. They run on the Quake
  Team's fighting AI:
  - **Choosing a target:** whoever is near, hurt, or hurt them last.
  - **When hurt:** they drink draughts and heal with skills.
  - **Retreating:** below their nerve (22-40% health) they fall back from every rival. They use their escape skills
    (disengage, smoke) or dodge rolls, rest a little and come back.
  - **Staying in:** they never leave the sand. Nothing they do reaches past the palisade, and a hero outside cannot hit
    them through the gate.

  A fallen adventurer is replaced a few seconds later. Adventurers grant no experience and drop no loot.
- **Level.** Adventurers are of the highest hero level in the party. A solo hero gets their own level.
- **Multiplayer.** The member who runs the outpost's combat runs the adventurers (`Net.is_world_authority`). That is
  the host whenever the host is at the outpost. Everyone else sees them as avatars. A blow between machines is
  resolved in two halves:
  - The attacker's machine applies the attacker's offense, against a bare target, and sends the damage per element
    (`Net.offense_pack`).
  - The owner's machine runs the target's defenses through the same pipeline (`Net.defense_request`) and sends back
    the number that landed, which the attacker sees.

  This protocol change raised `Net.PROTOCOL` to 14.
- **Falling.** A hero who falls on the sand gets no death screen and pays no cost: no gold, and no Phoenix Feather.
  Three seconds later they stand up just inside the gate with full health and mana, and nothing can touch them for
  2.5 seconds.
- **Companions.** While their hero is on the sand, Tempos, the Quake Team and guild fighters wait in the lane outside
  the gate (`Tempo._hold_back`). They cannot be hurt there and they fight nobody. They follow again as soon as their
  hero walks out.

## Where to tune

All of these constants are in `combat_budget.gd`. `test_bh028` checks each one.

- **Monsters hit too hard (or too soft) at every level:** change the monsters' authored damage. The curve shape is
  right.
- **Builds with no Strength or Wisdom die too easily:** raise `VITALITY_PER_LEVEL`.
- **Boss slams feel too weak:** raise `BOSS_MULT_SLOPE` (0.5), or raise `BOSS_DAMAGE`.
- **Duels end too fast:** lower `PVP_HIT_SHARE` (or `PVP_BLOW_CAP`).
- **The arena feels empty or crowded:** change `ArenaGrounds.FIGHTERS` (six).
