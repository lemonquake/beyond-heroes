# Class mechanics and eight hero saves

Existing saves and learned node IDs remain valid. Hero creation, Continue and Load Game now use eight slots. The Load Game list scrolls.

New signature passives use the existing skill-point system and scale from level 1 to 25. They are available in Knight/Shadowblade **Disciplines**, Ranger **Instincts**, and Mage **Mastery**. Existing talents and auras remain available. The Mage has a new **Gravity & Dark Arts** page.

| Class | Effect | Level 1 → 25 |
| --- | --- | --- |
| Knight | Steadfast | +15% → 60% knockback resistance; +3% → 15% block chance |
| Knight | Counter-attack (formerly Retaliation) | Block-triggered 120% weapon hit; 2-second cooldown; chance capped at 100% |
| Knight | Damage Return | Returns 10% → 40% of direct hit damage, before the attacker's defenses |
| Knight | Enduring Recovery | +0.1% → 0.5% maximum HP regeneration per second per distinct debuff; excludes the low-health indicator |
| Shadowblade | Double Attack | Extra hit after 0.12 seconds for 35% → 65% weapon damage; 1.2-second cooldown |
| Shadowblade | Paralyzing Attack | 30% → 85% movement slow for 0.1 seconds |
| Shadowblade | Bloodsucker | Every second successful basic melee attack heals for 10% → 35% of damage to its first target |
| Shadowblade | Bloodcurse | 20% → 70% reduction to all HP restoration for 4 seconds |
| Ranger | Knee Shot | 25% chance on basic ranged hits: +10% → 40% damage and a 0.4-second stun |
| Ranger | Split Shot | 30% chance on basic bow shots: 3 → 8 total arrows, each at 50% → 75% damage |
| Mage | Arcane Arts | 30% chance to refund 10% → 50% of the Mana actually spent on a spell |

Shadowblade attack passives apply to normal and heavy melee attacks. Repeated passive hits cannot trigger them again. A wide swing advances Bloodsucker once; a split volley hits each enemy at most once. Stuns respect resistance and existing immunity windows. Healing reduction affects potions, regeneration, lifesteal and elemental absorption. Bonus skill levels cannot exceed the listed attack-proc, healing-reduction, Mana-refund or stun caps.

Mage spells:

- **Gravity Pull:** instantly moves nearby enemies toward the selected center, then deals Dark damage. Body collision and knockback resistance limit the pull. 6 m radius, 9-second cooldown, 18 base Mana.
- **Spike Tentacle:** damages enemies in a 12 m line and stuns for 0.2–1.6 seconds. 6-second cooldown, 14 base Mana.
- **Meteor Strike:** updated existing Meteor, preserving its learned ranks and hotbar ID. 7 m radius, 90–130 base damage, 24-second cooldown, 45 base Mana, plus burning ground.
- **Mana Siphon:** drains up to 8–44 Mana per nearby enemy and restores only the amount drained. 7 m radius, 12-second cooldown, no Mana cost. Enemies now have a finite Mana pool of 30 + 3 per level; this pool does not alter their existing attack costs.
- **Dark Arts:** deals Dark magic damage and applies one random Weakened, Armor Broken, Silenced or Bloodcurse effect. 4-second cooldown, 12 base Mana.

Basic ranged attacks, aimed projectile skills, Frost Orb and Flame Sentinel retain target elevation. Cursor and touch targeting retain terrain height. Swept collision still stops shots at walls.

Verification uses `test_class_rework` for save roundtrips, the eight-card load menu, passive timing and limits, healing reduction, Mana conservation, control immunity, and stair/wall projectile fixtures. `test_skills` checks all definitions and live-casts every active skill for all four classes. Existing damage, status, progression and combat-growth suites are also run. The targeted suites passed 3,861 checks with zero failures. No manual playthrough is implied.

## Compiled builds

Godot 4.7.2 exports are available at `build/windows/BeyondHeroes.exe`, `build/BeyondHeroes-Windows.zip` and `build/BeyondHeroes.apk`. Windows is an x64 release with embedded game data and passed a headless startup smoke test. Android includes ARM64 and ARMv7 and uses the existing debug signing key; APK v2/v3 signatures and packaged class scripts were verified. Android was not tested on a physical device. SHA-256 checksums are in `build/build-checksums.json`; the committed build summary is `output/class-rework-build-summary.json`.
