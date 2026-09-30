# Equipment, damage, bosses, and rank audit

Implemented September 30, 2026. Balance target: a level-49 hero may one-shot ordinary enemies. Bosses should survive burst attacks, with an exceptionally geared Ranger reaching roughly 9,000–12,000 damage on a strong critical hit.

## What caused the problem

- Weapon damage retained inconsistent authored base budgets, then multiplied item-level growth, quality, tempering, and local physical damage. The highest local physical affix alone added 100%.
- Attribute damage, elemental damage, ordinary damage bonuses, and skill synergies multiplied across separate stages. Large skill weapon coefficients and critical multipliers compounded the result.
- Percentage-of-hit spell effects could receive outgoing bonuses and critical scaling again even though their source hit already contained those bonuses.
- Equipment comparisons omitted some bonuses used by combat. Bows and crossbows also used Strength in parts of the calculation despite their Dexterity requirements and Ranger progression.
- Story bosses could remain at their authored low level. Their health did not account for the player's equipment or skills, and there was no final boss burst protection.
- Random affixes, powers, and licenses were selected by equipment category without consistently respecting the item's intended class.
- The actual level cap was 60, despite the intended progression to 300. Ordinary enemy encounters lacked the requested world-level checkpoints.
- Promotion depended on a manual action, and the opening story requirements did not provide the requested automatic first promotion.

## Implemented rules

### Equipment and hero damage

Weapons above item level 5 use a common level-and-attack-speed damage budget. Their damage spread and attack speed remain distinct. Quality, tempering, and local physical damage add together. Local physical affix tiers are now 8–15%, 15–22%, 22–30%, and 30–40%.

Applicable attribute, elemental, weapon, projectile, general, and synergy increases share an additive budget. Investment above +200% has diminishing returns, approaching +500%. Attack weapon effectiveness above 200% also has diminishing returns, approaching 250%. Explicit situational multipliers remain separate. Hero critical damage is capped at 2.5 times a normal hit; maximum elemental resistance cannot exceed 90%.

Bows, crossbows, and javelins use Dexterity for their weapon scaling and flat physical attack contribution. Equipment comparisons use the same increased-damage calculation as combat, including added elements and both hands for dual wielding. Spell previews use the damage pipeline.

Inherited percentage-based spell procs and reflected damage no longer receive a second set of outgoing increases, positive situational multipliers, or critical rolls. Weapon-based attacks still receive their normal scaling.

### Bosses and enemy progression

New ordinary encounters advance to a level floor at 30, 45, 60, 75, 90, 105, and every 15 levels thereafter through 300. Higher authored levels are preserved. Checkpoints also add modest health and damage bonuses. Ordinary enemies have no new per-hit damage cap.

Bosses match the hero's level, preserving any higher authored level. At spawn, their health is calculated from a snapshot of the hero's sustained weapon damage, learned offensive spells, difficulty, and a level-based minimum. The initial health estimate uses a 25–45 second basic-attack budget before ordinary defenses, movement, and skill use; this is a tuning estimate, not a guaranteed fight duration. The level-based minimum prevents spawning a trivial boss by temporarily unequipping a weapon. Health does not change in response to gear swaps during the encounter. The encounter multiplier is included in network spawn data.

Bosses take 50% damage after ordinary defenses. Each final damage event is limited to the smaller of 8% of maximum boss HP and a level-based ceiling. The ceiling is 12,000 at level 49 and grows with the weapon budget at other levels. The rule applies to attacks, spells, damage-over-time ticks, impact, and inherited procs. For a 100,000-HP level-49 boss, the 8% rule permits at most approximately 8,000 damage per event. Damage components are scaled together before final integer rounding.

This protects individual damage events. It is not a time-based limit on combined party damage or several simultaneous projectiles; those still need encounter playtesting.

### Class equipment and existing saves

Class-labelled equipment excludes incompatible affixes, class powers, and licenses. For example, Knight gear cannot randomly receive Mage damage/casting affixes or Ranger projectile/focus/trap affixes. Elemental damage rolls on class weapons match their innate element. Neutral equipment continues to support hybrid builds.

Existing items receive a versioned, deterministic correction when loaded. Old local physical rolls retain their percentile within the new tier; incompatible rolls are replaced with eligible rolls. Item identity, name, upgrades, quality, sockets, masterwork status, and affix count are retained. Saving and loading again does not repeat the correction.

### Automatic ranks

At level 2 or higher, completing all four opening deeds (`mq_maelis_orders`, `south_gate_open`, `mq_shard_taken`, `mq_three_told`) awards Class E to an unranked hero without choosing a guild for them. A registered hero can automatically reach Class D after those deeds; D no longer requires a fee or guild jobs.

Later ranks still require every configured level, deed, achievement, membership, and gold requirement. Promotion checks run after relevant progression events and save loading. Fees are deducted once, and incomplete requirements prevent advancement.

## Measured results

Deterministic level-49 fixtures use real equipment generation, legal Ranger skill/talent allocations, and the actual boss damage pipeline. They are reproducible regression examples, not a survey of every possible build.

| Case | Result |
| --- | --- |
| Screenshot-style bow, 14% quality | Approximately 318–658 weapon damage |
| Screenshot-style crossbow, 14% quality, local physical masterwork | Approximately 707–1,068 weapon damage |
| Crossbow/bow base weapon DPS ratio | 1.405, including their different attack speeds |
| Sample Master-geared Ranger maximum tested boss critical | 7,082 against about 100,243 HP |
| Stacked Aether-geared Ranger critical | 7,945 against about 160,622 HP |
| Same Aether build with the tested 40% damage-taken mark | 11,123 against about 160,622 HP |
| Actual first story boss spawn for the Master fixture | Level 49, about 100,243 HP |

The screenshot recreation controls the stated quality and local physical roll. These weapon ranges are not a reconstruction of every hidden upgrade or secondary affix on the original saved items. Rarity alone does not determine damage: rolled stats, weapon choice, and build matter.

## Validation and limits

- Main balance, damage, stats, item, guild, progression, class, and boss-set suites: **13,068 checks, zero failures** (`output/balance-audit-final.log`).
- Related crafting, dungeon growth, loot, network, skill, status, team loot, and Tempo suites: **56,309 checks, zero failures** (`output/balance-audit-regressions.log`). The test process reported object/resource cleanup warnings at exit; its checks completed and exit status was zero.
- New strict regression suite: `game/tests/unit/test_balance_audit.gd`. It covers the reported weapons, deterministic save correction, generated sets, progression checkpoints through 300 for all four classes, a legally allocated Ranger burst build, real story-boss spawning, equipment-preview parity, extreme damage inputs, boss difficulty, and rank prerequisites/idempotence.
- Windows release export completed successfully with Godot 4.7.2. The exported executable completed a headless startup smoke check with exit status zero (`output/balance-audit-export.log`, `output/balance-audit-smoke.log`). Build: `build/balance-update/BeyondHeroes.exe`.
- An attempted full run reached the long live combat balance simulations but exceeded its 300-second timeout. The full suite is therefore **not** claimed to pass. These formula and regression checks do not establish complete class parity, multiplayer encounter duration, or subjective fight quality. A rendered playthrough of the opening story and representative late-game boss fights remains useful for tuning.
