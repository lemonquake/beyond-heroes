# Beyond Heroes — Elemental Damage Matrix

Rows: attacking element. Columns: defender affinity. Values multiply damage before numeric resistance.

| Attack \ Affinity | Fire | Ice | Lightning | Earth | Wind | Water | Light | Dark |
|---|---|---|---|---|---|---|---|---|
| **Fire** | _0.50_ | **1.50** | 1.00 | 1.00 | 1.00 | _0.75_ | 1.00 | 1.00 |
| **Ice** | _0.75_ | _0.50_ | 1.00 | 1.00 | **1.50** | 1.00 | 1.00 | 1.00 |
| **Lightning** | 1.00 | 1.00 | _0.50_ | _0.75_ | 1.00 | **1.50** | 1.00 | 1.00 |
| **Earth** | 1.00 | 1.00 | **1.50** | _0.50_ | _0.75_ | 1.00 | 1.00 | 1.00 |
| **Wind** | 1.00 | _0.75_ | 1.00 | **1.50** | _0.50_ | 1.00 | 1.00 | 1.00 |
| **Water** | **1.50** | 1.00 | _0.75_ | 1.00 | 1.00 | _0.50_ | 1.00 | 1.00 |
| **Light** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | _0.50_ | **1.50** |
| **Dark** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.50** | _0.50_ |

Physical attacks and neutral (no-affinity) defenders always use 1.00.

## Relationships

- **fire>ice** — Fire melts ice.
- **ice>wind** — Ice stills and freezes moving air.
- **wind>earth** — Wind erodes stone and scatters dust.
- **earth>lightning** — Earth grounds lightning.
- **lightning>water** — Water conducts lightning.
- **water>fire** — Water douses fire.
- **light>dark** — Radiance burns away corruption.
- **dark>light** — Corruption devours the holy.
- **same** — Creatures of an element shrug off half of that element.
- **reverse** — Attacking against the wheel is 25% weaker (e.g. Ice into a Fire creature melts).
- **physical** — Physical damage ignores affinity; Defense and Physical Resistance handle it.

## Element identities

- **Physical** (builds `stagger`): Raw force. Mitigated by Defense; builds Stagger.
- **Fire** (builds `burning`): Burning: damage over time. Offensive pressure. Spreads with Wind.
- **Ice** (builds `chilled`): Chill slows; Chill buildup becomes Freeze. Wet targets freeze twice as fast.
- **Lightning** (builds `shocked`): Shock: target takes more damage. High burst, can chain. Wet targets are shocked harder.
- **Earth** (builds `stagger`): Stagger and impact. Ignores 25% of armor. Heavy hits stagger more.
- **Wind** (builds `windswept`): Knockback x1.5 and mobility. Fans Burning onto nearby foes.
- **Water** (builds `wet`): Wet: conducts Lightning, speeds Freeze, extinguishes Burning.
- **Light** (builds `purged`): Radiant. Purges enemy regeneration and buffs; heals the caster on hit.
- **Dark** (builds `cursed`): Curse amplifies all damage taken; Dark hits drain life.

## Interactions (StatusController)

- **Wet + Lightning** — Lightning damage x1.25, Shock buildup x2, Shock strength 25% instead of 15%.
- **Wet + Ice** — Freeze buildup x2.
- **Burning + Water** — Water extinguishes Burning and leaves the target Wet.
- **Wet + Fire** — Fire damage x0.8 and the Wet status evaporates.
- **Fire vs Chilled/Frozen** — Fire thaws: removes Chill and Freeze buildup.
- **Frozen + heavy physical / impact** — Shatter: physical damage x1.3, Freeze ends.
- **Earth + strong physical impact** — Earth share adds up to +50% poise (stagger) damage.
- **Wind + Burning** — Wind hits fan Burning onto enemies within 4 m.
- **Light + Cursed** — Purify: light damage x1.3 and the Curse is consumed.
- **Freeze immunity** — after Freeze ends the target cannot be frozen for 4 s (no permanent freeze-lock).
- **Stun immunity** — 3 s after a stun ends.
