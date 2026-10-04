# Class Transcendence: major progression implementation brief

Prepared by Codex for Claude Code on 3 October 2026. Project: `A:\Python\beyond-heroes`.

**PRIORITY: VERY HIGH. This is a major, required gameplay addition. Treat progression, all twelve new classes, working skills and talents, equipment requirements, old-save compatibility, and multiplayer presentation as one complete feature. Do not reduce this request to class names, recolored models, placeholder abilities, or future-work notes.**

The user appointed Codex to plan and orchestrate this work and Claude Code to implement it. This file is the implementation handoff. Codex has inspected the existing systems and prepared the design; none of the proposed gameplay changes are already implemented by this brief.

## 1. Start here

Read this entire file, applicable repository instructions, `docs/LORE.md`, `docs/COMBAT_SCALING.md`, `docs/BOSS_SETS.md`, `docs/ASCENDANT_TIERS.md`, `docs/SPECIAL_WEAPONS.md`, and `docs/OFFICIAL_SERVER.md`. Inspect the current working tree before editing. There are existing uncommitted changes in gameplay, networking, visuals, tests, and the account service. Preserve them, understand their intent, and build on their current implementations. Do not reset, discard, overwrite, or include unrelated changes accidentally.

Complete an in-progress write/import/export safely before starting this milestone. Then make this the next major feature milestone. Keep existing beta stability, performance, world polish, gear-balance, and multiplayer work intact. Do not use the older briefs' release/push authorization as a reason to publish this feature before its evidence has been reviewed. This handoff requests implementation and verification, not a production-server update or an automatic commit/push.

Work through the stages in section 12 in order. Keep a short progress report with concrete completed work, failures, and evidence paths. Resolve ordinary implementation choices yourself. Ask only when a missing external resource or incompatible user requirement prevents meaningful progress.

User writing requirements apply throughout: plain, readable labels; no slogans, sales copy, military framing, or tiny uppercase information. Use labels such as Class, Skills, Talents, Transcend, Choose Master Class, Confirm, Cancel, Team, and Play. Fantasy class names explicitly requested here, including Royal Guard and Dark General, remain valid class names.

## 2. Required progression rules

There are four starting classes and twelve additional classes: sixteen identities in total. Each starting family has one first transcendence and two mutually exclusive second-transcendence master choices.

| Starting class | Level 60: first transcendence | Level 120: master choice A | Level 120: master choice B |
| --- | --- | --- | --- |
| Knight | Royal Guard | Dark General | Grand Paladin |
| Hunter | Tracker | Wildwarden | Starstrider |
| Mage | Arcanist | Archmage | Void Sovereign |
| Shadowblade | Nightstalker | Phantom Reaper | Blood Sovereign |

The game currently calls the Hunter family **Ranger**, with internal ID `ranger`. Use **Hunter** as the player-facing starting-class name. Keep `ranger` as the canonical saved/runtime family ID. Existing Ranger saves, items, trees, models, and references must continue to resolve. Historical changelog entries can retain their original wording. Do not perform a global ID rename.

Required behavior:

- First transcendence is available at **level 60**, inclusive; the second at **level 120**, inclusive. There are exactly two advancements for now, including at levels 180, 240, and the existing cap of 300.
- Visit a **Grand Master in any Guild House** to advance. This is a public service: guild membership, guild letter rank, quest completion, gold, materials, and a purchased item are not prerequisites.
- The second advancement requires the first. At level 121 or 300, a previously unadvanced hero can complete the first advancement, then immediately choose a master class in the same Guild House session.
- Crossing a level threshold grants eligibility; it does not automatically pick a class. Display a clear notice and a persistent, unobtrusive reminder in Character/progression UI. A missed notice or an old save must not lose eligibility.
- Transcendence preserves level, XP, attributes, allocated points, base abilities, earlier transcendence abilities, inventory, equipment, guild, rank, quests, Tempos, appearance customization, checkpoints, and world progress. It never resets the hero to level 1 or reruns new-character setup.
- Each advancement grants **three new active skills at rank 1 and three new talents at rank 1**, once. They are actual content, not merely three generic point bonuses. A master hero gains six new active skills and six talents along the selected path. The alternative master branch remains unavailable.
- Rank 1 of these six grants is earned class content, cannot be refunded into points, and survives ordinary respec. Additional ranks use normal skill/talent points and refund only the points actually spent. There is no extra unrestricted point windfall.
- Keep the existing six-slot skill bar. Add skills to empty slots only; never replace a full bar. Tell the player that the new skills can be assigned from Skills. Base and first-stage skills remain usable.
- Master choice is permanent in this update, with a review and explicit confirmation before saving. Normal attribute/skill/talent respec does not change it. Do not add a paid master-switch economy.
- A failed validation, duplicate click, stale window, reopened dialogue, reconnect, or repeated load must not repeat rewards. Confirm against current hero state rather than cached UI state.
- Ordinary offline transitions complete and save through the normal durable save path. Official-account transitions use the established official save path, with a clearly reported pending/failure state and safe retry. Do not announce a durable online success before persistence is acknowledged.

Eligibility is derived, not a stored currency:

`eligible_steps = min(2, floor(level / 60))`

`available_steps = max(0, eligible_steps - completed_steps)`

The level requirement and predecessor must still be checked at the actual advancement boundary. The user explicitly requested retroactive eligibility for old saves; no replay of level-up events is needed.

## 3. Class identities, themes, and content

Reuse each family's underlying combat resource: Knight Valor, Hunter Focus, Mage Arcane Charge, and Shadowblade Combo. Advancement deepens that playstyle instead of replacing it with an unrelated resource system. Retain base growth and progression curves; the authored grants provide the new power. Do not recompute all historical levels using inflated descendant growth.

The tables below define the required abilities and talent identities. Each skill entry gives an intended behavior and an initial cooldown in seconds. Claude must author real numerical damage/scaling, Mana/resource costs, ranges, duration, rank progression, weapon restrictions, animations, sounds, VFX, and honest tooltips in a balance sheet before final tuning. Initial cooldowns and talent values are design starting points, not claims that they are balanced already.

Use the existing damage/status/resource pipelines. Weapon attacks scale from the relevant weapon; spells scale through the existing spell stats and combat budgets at levels 60–300. A small level-1 flat spell damage value alone is insufficient. Respect line of sight, walls, collision-safe movement limits, friendly/enemy masks, immunities, animation hit timing, and authoritative world-effect routing already used by the game.

Use stable namespaced IDs, e.g. `rg_bastion_rush`, `gp_dawn_verdict`, and `vs_event_horizon`. Prefixes must distinguish Void Sovereign from other branches. Each of the twelve new identities has exactly three newly authored active skills and three talents. Skills may use existing parametric behavior routines, but their combinations must create the distinct mechanics described here.

### Knight family

| Class | Role and theme | Three skills | Three talents |
| --- | --- | --- | --- |
| **Royal Guard** (`royal_guard`) | Defensive melee and protection. Royal blue `#527ED6`, restrained gold `#D8B46A`. | **Bastion Rush**: collision-safe shield charge, stagger and knockback on its struck targets; requires shield; 10 s. **Sovereign's Challenge**: short-range challenge redirects nearby enemies' targeting to the caster and grants brief damage reduction; bosses resist forced targeting without erasing the defensive benefit; 18 s. **Bulwark Standard**: one bounded ground zone grants allies block/poise protection while inside; no shield required for the zone itself; 24 s. | **Crown Discipline**: increased block strength. **Unbroken Line**: increased poise and knockback resistance. **Guardian's Resolve**: modest extra Valor on successful blocks, with a per-event cap. |
| **Dark General** (`dark_general`) | Aggressive armored melee, dark damage and pressure. Charcoal `#343444`, crimson `#C9566C`. | **Dread Cleave**: wide weapon sweep partly converts physical damage to Dark and briefly weakens targets; 9 s. **Warbound Advance**: controlled dash followed by a heavy strike, with brief stagger resistance; 14 s. **Black Dominion**: a short-lived dark zone deals bounded pulses and spends Valor once to strengthen its initial hit; 30 s. | **Dreadsteel**: increased physical/Dark damage, within one damage budget. **Relentless March**: modest movement speed during combat. **Iron Tyrant**: a capped, cooldown-limited barrier after spending Valor on a skill. |
| **Grand Paladin** (`grand_paladin`) | Light melee and team protection. Ivory `#E8E0C6`, warm gold `#E5BD64`. | **Dawn Verdict**: heavy weapon hit partly converts damage to Light and consumes Valor once for bonus damage; 10 s. **Sanctified Ground**: a small zone deals Light pulses to enemies and modest healing to allies; both are independently capped; 24 s. **Oath of Mercy**: cleanse one eligible harmful status and grant a short barrier to the caster and nearby allies; 28 s. | **Radiant Steel**: increased physical/Light damage. **Merciful Oath**: increased outgoing healing/barrier strength. **Hallowed Armor**: modest increased defense and Light/Dark resistance using existing resistance caps. |

### Hunter family

| Class | Role and theme | Three skills | Three talents |
| --- | --- | --- | --- |
| **Tracker** (`tracker`) | Marks, pursuit, and traps. Moss `#688C53`, amber `#D5B86A`. | **Quarry Mark**: marks one visible enemy; only the caster's eligible ranged hits receive the modest bonus; 12 s. **Snareline**: place a bounded line of snares with one activation per target per cast and immunity-aware roots; 16 s. **Trail Volley**: a directional fan of arrows/bolts; one initial hit per target from the fan; requires bow/crossbow; 10 s. | **Keen Trail**: modest accuracy and critical chance. **Patient Aim**: increased Focus gain at existing safe-distance conditions. **Fieldcraft**: increased trap effectiveness with duration caps. |
| **Wildwarden** (`wildwarden`) | Terrain control and nature-themed defense; no new pet system. Deep green `#39876A`, pale jade `#A3CF9C`. | **Briar Volley**: ranged fan that leaves a small slowing patch; overlaps do not multiply damage; 12 s. **Living Thicket**: one persistent area deals Earth-themed damage and applies short root/slow, respecting boss resistance; 24 s. **Warden's Refuge**: a short-lived shelter gives allies a modest barrier and resistance to slowing; 28 s. | **Thorncraft**: increased trap/area damage. **Rootbound Guard**: increased defense while standing in the caster's own active terrain, with one benefit regardless of overlaps. **Verdant Reserve**: modest increased maximum HP and potion healing effectiveness. |
| **Starstrider** (`starstrider`) | Long-range precision and controlled repositioning. Midnight blue `#495DB7`, starlight `#A5DCEC`. | **Astral Pierce**: a narrow piercing shot, partly converted to Light, with reduced damage after its first target; spends Focus once; 12 s. **Comet Step**: collision-safe evasive vault that empowers the next eligible shot for a short window; no permanent invulnerability; 18 s. **Constellation Rain**: limited arrow/bolt impacts in a selected visible area, with a per-target hit cap; 30 s. | **Celestial Sight**: increased damage beyond a defined distance, without extending network hit reach. **Comet Rhythm**: one small cooldown reduction per eligible critical event, with a global proc interval. **Steady Constellation**: modest reduced Focus decay; does not generate free Focus out of combat. |

### Mage family

| Class | Role and theme | Three skills | Three talents |
| --- | --- | --- | --- |
| **Arcanist** (`arcanist`) | Controlled casting, Mana use, and spell geometry. Violet `#946BD3`, silver `#C7D0E6`. | **Aether Lance**: aimed piercing arcane/Light spell through the existing element system; 8 s. **Runic Circle**: one area strengthens the caster's paid spells while inside; no repeat multiplicative stacking; 22 s. **Mana Ward**: a capped Mana-powered barrier with explicit cost, duration and cooldown; it does not convert all incoming damage into infinite Mana loss; 24 s. | **Runic Efficiency**: modest Mana cost reduction subject to a cost floor. **Charge Discipline**: slightly extends Arcane Charge retention. **Aether Precision**: increased spell accuracy/critical effectiveness supported by the existing pipeline. |
| **Archmage** (`archmage`) | Elemental combinations and broad-area spells. Sapphire `#497EC9`, white `#E0E7F3`. | **Prismatic Tempest**: bounded Fire/Water/Lightning pulses with documented status interactions and per-target cap; 30 s. **Grand Convergence**: a paid spell consumes Arcane Charge once for a powerful elemental blast; 24 s. **Spellweave**: arms one reduced-strength repeat of the next eligible paid spell; repeated spells cannot repeat/refund recursively; 28 s. | **Elemental Concord**: increased elemental damage against targets with distinct elemental statuses; counted/capped once. **Master Channeling**: modest cast speed. **Prismatic Shelter**: short, capped resistance benefit after spending charge, with an internal cooldown. |
| **Void Sovereign** (`void_sovereign`) | Dark gravity control and deliberate burst. Indigo `#5446A6`, pale violet `#B292EA`. | **Event Horizon**: one bounded gravity well pulls eligible enemies and deals Dark pulses; checks walls and knockback resistance; 28 s. **Null Lance**: piercing Dark spell with modest armor/resistance penetration through existing capped rules; 12 s. **Rift Collapse**: consumes Arcane Charge once for a delayed, clearly telegraphed explosion at a visible selected point; 30 s. | **Void Geometry**: modest increased area size, capped before hit queries. **Entropy**: increased Dark damage against cursed enemies. **Sovereign's Reserve**: modest maximum Mana and Mana regeneration; no permanent damage immunity. |

### Shadowblade family

| Class | Role and theme | Three skills | Three talents |
| --- | --- | --- | --- |
| **Nightstalker** (`nightstalker`) | Mobile melee, ambush windows, and Combo control. Plum `#8655A8`, steel `#ADB3C6`. | **Umbral Lunge**: collision-safe dash strike that builds Combo once on a successful cast, not once per incidental hit; 10 s. **Gloom Veil**: brief existing-system concealment/evasion window; attacking breaks concealment; 22 s. **Marked Execution**: Combo finisher with a modest bonus against a marked target; no automatic boss kill; 16 s. | **Ambush Training**: modest critical chance after a defined ambush. **Silent Footwork**: increased evasion/movement speed. **Patient Blade**: slightly extends Combo retention within a hard cap. |
| **Phantom Reaper** (`phantom_reaper`) | Precise repositioning and finishing burst. Cool violet `#7A77C9`, spectral blue `#BEDDEB`. | **Phantom Crossing**: short collision-safe reposition and strike, with a bounded evade window; 18 s. **Reaper's Arc**: wide Combo-consuming finisher with reduced damage against secondary targets; 20 s. **Afterimage Flurry**: limited secondary follow-up hits from the caster's position; not an AI summon; repeats cannot trigger other repeat-attack procs; 28 s. | **Ghoststep**: modest dodge cooldown reduction with a floor. **Reaping Edge**: increased finisher damage under a cap. **Untouchable Rhythm**: a brief modest evasion benefit after a valid dodge, with an internal cooldown. |
| **Blood Sovereign** (`blood_sovereign`) | Bleeding melee and bounded self-sustain. Garnet `#AD4B64`, rose `#DF9C9C`. | **Crimson Rend**: weapon attack applies a bounded bleed; 10 s. **Sanguine Pact**: spend a small current-HP cost safely, never killing the caster, for a short damage/lifesteal window; 26 s. **Blood Eclipse**: Combo-consuming area finisher deals extra damage to bleeding targets and heals only from actual damage dealt, under a cast-wide cap; 30 s. | **Hemomancy**: increased bleed damage. **Sovereign's Hunger**: modest increased lifesteal effectiveness under the existing total cap. **Crimson Endurance**: modest increased maximum HP and healing effectiveness, without canceling Bloodcurse. |

### Numerical authoring and grant accounting

Use the existing 25-rank framework for active skills and ordinary ranked talents. For ranked transcendence talents, author conservative rank-1 values and diminishing progression: roughly 2–4% increased damage/defense/effectiveness, 1–2% movement/cast speed, or 0.5–1 percentage point critical chance as starting scales. Avoid confusing percentage points with increased-percent multipliers. Mechanic-changing talents may be one-rank major nodes with a fixed bounded effect.

`TreeDef.finalize_levels()` currently changes most node caps to 25 and retains an authored `base_rank` for diminishing returns. `SkillDef.resolve()` also supports item bonus skill ranks. Author around these real rules and test maximum investment plus the existing +5 item skill levels; do not write descriptions assuming a five-rank cap that runtime silently changes to 25.

All base/granted rank floors need centralized accounting. Do not simply inject ranks and let `points_spent`, refund, reset, or legacy sanitization treat those free ranks as paid points. Track or derive earned floors from valid class history. Show both free-granted and paid ranks correctly. Rebuild missing earned floors idempotently on load/respec without awarding points. Grant floors can count as learned prerequisites, but must not count as paid tree investment unless an explicitly documented tree rule calls for it.

## 4. State and architecture

Preserve `HeroData.cls` and saved `hero.class` as the **starting family**. Existing combat behavior, resource code, trees, model selection, official account rules, and import identity use those IDs. Do not change a Knight's saved `class` to `grand_paladin` and try to repair every family switch afterward.

Add a data-driven class advancement registry and one progression service with methods equivalent to:

- `base_family(hero)`, `current_class_id(hero)`, `current_class_name(hero)`;
- `completed_steps(hero)`, `eligible_steps(hero)`, `available_steps(hero)`;
- `lineage(hero)`, `valid_next_choices(hero)`, `can_transcend(hero, target)`;
- `transcend(hero, target)`, `earned_rank_floors(hero)`;
- `class_theme(class_id)` and the shared requirement evaluator in section 6.

Persist a small optional, versioned field, for example:

```json
"transcendence": {
  "schema": 1,
  "path": ["royal_guard", "grand_paladin"]
}
```

The path must be valid for the saved base family, have at most two steps, have the required predecessor and level, and contain at most one master choice. Derive identity and granted content from it. Never trust a saved display string, color, glow flag, eligibility count, or duplicate rewards list as class authority.

Build composed skill/talent trees **per hero or per immutable identity**, retaining all base node IDs and ranks. Do not append branch nodes into a shared `DB` tree when one hero advances: that leaks locked content into other heroes and previews. Rebuild indices/connections safely and keep existing UI selection and ranks. Load and validate advancement state before loading branch ranks/equipment. The current `HeroData.from_dict()` loads equipment and trees early, so ordering needs attention.

Gate class-specific content at allocation, learned/passive enumeration, skill resolution, hotbar assignment, cast execution, and persistent modifiers. A forged rank or direct `SkillRunner` invocation must not grant the sibling master branch. Item +skill levels never unlock an unlearned or wrong-class ability. Preview/catalogue calculations must use an explicit preview identity without bypassing real-player checks.

## 5. Old saves and official accounts

Missing transcendence state means the original starting class, with eligibility derived from the current level. The old hero is never auto-assigned a master choice. A level-121 old save must be able to become Royal Guard, then choose either Knight master branch immediately; apply equivalent tests to all families.

Current inspected versions: `SaveSystem.CURRENT_VERSION = 4`, `server.service.SAVE_VERSION = 4`, and both network/account protocols are 19. Recheck them at implementation time because work is ongoing.

Preferred persistence approach: add an optional `transcendence.schema = 1` while retaining the compatible v4 save envelope. Add normalization and validation for this field to **all** load/import/account paths. The old-save transformation is additive; existing versions 1–3 must still pass their existing migrations before the new state is normalized. If the actual implementation requires a new envelope version, update every producer/validator/import path together and explicitly support upgrading existing official stored characters. Do not blindly increment a constant and make all stored accounts unloadable.

Offline malformed progression should recover conservatively to the longest valid prefix with an explanatory diagnostic. Wrong-branch saved ranks must not become active. Preserve legitimate earlier ranks and investments; distinguish verifiable paid allocations from free grants before refunding, so corrupt/unknown data cannot mint points. Official submitted malformed state should be rejected with an actionable error. Existing saved characters with no new field remain valid.

Keep official base-class immutability. `server/service.py` currently rejects unknown base classes and changes to `hero.class`; that protection should remain. Add typed validation of the advancement path and monotonic transition checks: no reversal, sibling switching, predecessor skip, or advancement below its level. Catch-up can extend by both valid steps for a high-level legacy hero. New-character creation starts with an empty path. Include the effective class/path in the character-card and ticket-redeem payloads, keeping the base-class field where existing consumers require it.

Refresh official profiles from accepted persisted advancement data. Do not allow a client cosmetic claim alone to award a master title or glow. Inspect save acknowledgment, ticket redemption, reconnect, character switching, rollback/failed upload, and character-card refresh as one flow. Existing combat remains subject to the documented client-simulation limitations; do not claim this change makes the entire game server authoritative.

Preserve `SaveSystem.legacy_identity`: transcendence and the Ranger/Hunter label change must not make one imported hero acquire a new identity and be imported twice. Preserve backup/recovery behavior. Test using copied fixtures and isolated test account storage, never rewrite the user's actual save files or live account database.

## 6. Equipment requirements: one shared rule system

**Required: all equipment must clearly explain which classes can equip it, and the rule must actually be enforced.** Inspect every equipment source, including ordinary gear, artisan gear, boss sets, special/story weapons, relics, Ascendant tiers, merchant stock, crafting, enchanting, and debug previews.

Implement explicit requirement kinds rather than overloading drop preferences:

| Requirement kind | Meaning | Example text |
| --- | --- | --- |
| Any | Every hero class can equip it, subject to other requirements. | `For any class` |
| Family | Starting class and every descendant in that family. | `For Knight class` followed by `Includes Royal Guard, Dark General, and Grand Paladin` where helpful. |
| Lineage | Named advancement and its descendants. | `For Royal Guard and its master classes` |
| Exact class | Only the current named class. | `For Grand Paladin only` |
| Explicit alternatives | A documented union of permitted families/identities. | `For Hunter or Shadowblade classes` with descendant semantics made explicit. |

Use stable IDs and validate references centrally. Family matching must not be string-prefix matching. Lineage matching must follow registry ancestry. Exact matching must not accidentally include a sibling or a base hero. Other gates combine with AND: class, character level, attributes, equipment slots/hands, rarity/guild rank, and story/Tempo rules.

`ItemBaseDef.class_hint` is currently a **preference** for loot/shop fit; do not silently turn every hint into a hard lock. Audit intended ownership and author a complete requirement manifest. Ordinary broadly usable gear can remain `For any class`; class-themed weapons/sets should receive explicit justified family requirements. Existing `wearers` already includes hero and **Tempo** IDs; retain its stricter story restrictions and explicit Tempo permissions. Tempo classes do not gain player transcendence automatically. A new master-only item is unavailable to a Tempo unless deliberately authored otherwise.

Use one evaluator/text formatter in actual equip checks, inventory and compare tooltips, shops, crafting/reward previews, Lape's requirements, trade/showcase views, save-load equipment repair, and class-fit loot decisions. Tooltips should work even without a current hero. Show unmet requirements in readable text plus color; do not rely on color alone. Distinguish `Class: Grand Paladin` from the existing guild letter-rank requirement. If needed, clarify equipment rank labels as `Guild rank B required` while retaining current rank rules.

Unbound equipment may bypass its existing level/attribute gates as before, but **does not bypass class ownership**. Selling, storing, or trading an incompatible item remains allowed; the recipient cannot equip it until eligible. Enchanting, upgrading, reforging, sockets, rerolling, and serialization preserve requirements. Equipping family gear stays valid after transcendence. Do not make the earlier advancement's own gear exact-only and force it off on reaching master.

If newly authored legitimate restrictions invalidate already equipped legacy gear, remove its combat contribution deterministically and preserve the exact instance in inventory or the existing persisted `Equipment.recovered_items` queue when the bag is full. Keep identity, rarity, sockets, gems, powers, licenses, upgrades, and ownership. Inform the player how to recover it; no deletion, reroll, duplication, or silent stat application while in recovery. Avoid unnecessary restrictions on genuinely shared existing items.

## 7. Required new gear and acquisition

Add **three real gear bases per new class**, thirty-six total: a signature weapon, armor, and accessory. First-stage pieces use lineage requirements and minimum level/drop band 60; master pieces use exact master requirements and minimum level/drop band 120. Use existing weapon/armor slots, class mastery, item budgets, rarity/rank gates, and available model/icon fallbacks. A first-stage item's requirement must remain valid for either master descendant.

| Class | Signature weapon | Armor | Accessory |
| --- | --- | --- | --- |
| Royal Guard | Crownward Longsword | Royal Guard Cuirass | Oathkeeper Seal |
| Dark General | Dreadmarshal Greatsword | Black Dominion Plate | Dread Command Signet |
| Grand Paladin | Dawnstar Longsword | Sanctified Plate | Sunward Reliquary |
| Tracker | Trailkeeper Bow | Tracker's Leathers | Quarry Compass |
| Wildwarden | Briarheart Bow | Livingwood Leathers | Wildroot Pendant |
| Starstrider | Starfall Crossbow | Constellation Leathers | Comet Lens |
| Arcanist | Runebound Staff | Arcanist Vestments | Runic Focus |
| Archmage | Prismatic Staff | Archmage Robes | Convergence Prism |
| Void Sovereign | Eventide Staff | Riftwoven Robes | Horizon Core |
| Nightstalker | Gloamfang Dagger | Nightstalker Leathers | Silent Trail Charm |
| Phantom Reaper | Wraithedge Dagger | Afterimage Mantle | Reaper's Glass |
| Blood Sovereign | Crimson Oath Dagger | Sanguine Leathers | Bloodmoon Signet |

Do not grant all equipment freely on advancement. Give each piece a real documented acquisition route using the current themed loot and/or recipes, with materials that are actually obtainable. At least one reliable post-advancement route per identity should let the player pursue appropriate gear without relying on an unspecified future dungeon. A Grand Master gear catalogue or existing appropriate merchant/crafting integration is acceptable; retain existing shop/rank affordability rules and ensure source reachability at the intended level.

For optional item powers, author at most one bounded class-skill interaction per signature piece. Keep ordinary gear a viable alternative; do not bake a mandatory enormous multiplier into every new item. Include total budgets and source IDs in the catalogue. Reuse the newest loot-pool/Ascendant work rather than adding a competing random global reward path. Update weighted class-fit functions to understand the hero's family and effective class without making every drop personal or excluding tradeable off-class drops. A branch item must never drop below its configured drop band.

## 8. Grand Master and advancement UI

Add a distinct **Grand Master** NPC/service to every existing Guild House map. The currently inspected public Guild House is `int_guildhouse`, built by `game/src/world/maps/interior.gd`, with NPCs in `DataNpcsGuildHouse`. Audit actual maps rather than treating every guild banner/counter as a separate building. Register the service through the existing dialogue/UI system so future Guild House definitions can reuse it.

Suggested NPC: **Grand Master Edran Vale**, using an existing suitable model, an appropriate portrait, and a reachable location that does not block Hollis, the board, doors, counters, or navigation. Respect existing NPC portrait baking/fallback conventions. Add directory/navigation guidance so the hero can find the service.

Window content:

- Current class, base family, level, completed advancements, and next requirement.
- At stage 0: the first-stage preview with its role, three skills, three talents, theme, and accessible `Transcend` button when eligible.
- At stage 1: two side-by-side master cards showing role, full skill/talent summaries, theme preview, representative exclusive gear, and explicit permanent-choice text. Choose a card, review, then Confirm or Cancel.
- Below requirement: explain `Requires level 60` or `Requires level 120 and Royal Guard`, using the correct family. Allow previewing locked branches.
- At stage 2: show the selected master class and its full lineage. State that both available advancements are complete. Do not promise a third one.
- After first advancement of a level-120+ hero, refresh immediately to master choice; no extra level, relog, guild join, or second-building visit is needed.

Add distinct first-stage/master pages to Skills and Talents, including locked previews where appropriate. Talents currently has no tab strip equivalent to Skills, so adapt its layout deliberately. Show the three granted nodes per stage and their earned rank floors. Preserve existing tree pages, ranks, connections, learned-skill list, skill details, hotbar assignment, and respec UI. Apply the effective class name consistently to Character, save/account cards, team/party panels, Showcase, and progression summaries. New-hero creation still offers only the four starting classes.

Readable desktop and touch layouts are mandatory. Verify 1280×720, 1920×1080, and the project's current phone layout; use scrolling instead of clipping requirements or squeezing text into tiny uppercase captions. Class descriptions explain mechanics directly without slogans.

## 9. Multiplayer floating class text, themes, and master glow

**The user's additional requirement is mandatory:** other players must see each hero's **current class in the existing floating display beneath the character's name**. Transcendent identities have different color themes. Master classes have an epic but **subtle glow**. The user explicitly clarified that the existing positioning must stay unchanged.

Preserve the existing floating-label order and layout, updating the class identity in place:

```text
PlayerName
Level 121 Grand Paladin · PC
```

The class remains in the current line beneath the player's name, and health/revive/team information remains legible. Starting and first-stage heroes also show their correct class (`Hunter`, `Tracker`, etc.). Do not show only `Knight` for all three Knight descendants. Do not display the class only in Team or Character panels.

The existing `NetAvatar` has `_tag` and `_sub` `Label3D` nodes, with the current base class embedded below the name in `_sub.text`. Update that class identity in place; preserve its positioning and do not add a duplicate class line or move the class above the name. Preserve camera-facing behavior, adequate dark outlines/contrast, visibility rules, and spacing so adjacent players, different model heights, gear, HP bars, and revive cues remain readable. Retain personal/team color on the name or identity marker; apply class theme to the existing class-containing line and subtle class accents. Text identity must remain clear without color discrimination.

All twelve themes are specified in section 3. Keep each base class's familiar theme. Master presentation adds a restrained rim/emissive accent and/or small foot-level halo with slow movement. It must be visible locally and on remote human heroes, including without bloom, while leaving body, weapons, gear, telegraphs, and floating text readable. First-stage heroes get their theme but not master glow. Give each master a recognizable accent using its own theme; avoid a giant shared neon ring.

Preserve custom skin/hair/clothing dyes, gear materials, weapon visuals, existing set effects, stealth, hit flashes, death/dissolve, quality settings, and the current appearance-revision synchronization. Do not tint every material indiscriminately or overwrite shared imported material resources. Compose per-instance accents safely with existing `material_overlay` uses. Glow should fade appropriately when stealthed/dead and stop/clean up on despawn/map change. It never affects damage, targeting, lighting gameplay, or physics.

Use a bounded inexpensive effect: no added real-time shadow light per master, no full-screen effect, no per-frame network color/particle replication, and no per-frame material reallocation. Derive effects from a class ID locally. Lower quality may remove optional motes while retaining the subtle rim/halo and readable class line. Measure an all-master group, not only one hero in an empty scene.

### Network and account integration

Keep the `cls` profile field as the stable starting family for existing consumers. Send a small validated path/current identity alongside it. Derive the visible label/theme from the registry and validate its consistency with family, level, and path. Never accept arbitrary peer-provided text, shader paths, colors, effect intensities, or material names as class presentation.

Update `Net._profile`, `NetGuard.clean_profile` (which currently drops unknown keys), join/roster/profile update flow, `NetAvatar`, appearance setup/rebuild, team summaries, Showcase, official character cards/ticket redemption, and any compact encoding affected by the change. The official join path replaces profile class information from stored character metadata; include advancement there. The official `_profile_changed` path locks base identity fields; ensure effective class refresh is deliberately validated through accepted save metadata rather than lost or blindly trusted. Account for ordering/races between save acknowledgment and profile broadcast.

Broadcast class/theme changes on successful advancement, not only level-up. Already-connected peers must see it promptly without map reload. Validate first roster arrival before appearance arrives, late join, same-map advancement, map change, appearance revision update, gear change, reconnect, dedicated-server relay, and world-host handoff. Build/rebuild once when identity actually changes, not every snapshot. Only human player avatars receive this player-class title/glow; do not reclassify Tempos or NPCs from their owner's class.

This affects required visible class metadata. Coordinate a network protocol bump from the actual current version (inspected: 19) in client/account/coordinator compatibility checks, discovery and tests. Do not mix old/new peers silently if old clients would erase or misrepresent advancement. Handle stored legacy saves through migration/normalization separately from network version mismatch. A meaningful incompatible-client error is part of completion.

## 10. Balance and future dungeon requirements

Use equal **content counts**, not identical mechanics. Each master branch needs a reason to choose it and a clear limitation: Dark General offense vs Grand Paladin support; Wildwarden control vs Starstrider precision; Archmage elemental breadth vs Void Sovereign Dark control; Phantom Reaper burst/evasion vs Blood Sovereign bleed/sustain.

Balance at identical character level, gear, invested point budget, and scenario. Compare at levels 60, 120/121, 180, and 300. Include grant-only builds, substantial rank investment, max ranks/+skill equipment, full themed equipment, solo enemies, bosses, and teams. New sustain, cooldown refunds, repeat attacks, damage return, and spell repeats must not recursively generate themselves or each other. Check existing Split Shot, Double Attack, Bloodsucker, Bloodcurse, Arcane Arts, Spell Echo, auras, mark bonuses, and new class-specific item powers.

Initial targets to test and tune, not invent as already achieved:

- At equal loadout/level, a first advancement's grant-only package should be a meaningful roughly 10–20% sustained-combat benefit in its intended use. A second advancement adds another roughly 10–20% relevant benefit. Measure damage and defense/support separately; never sum every metric into one fake score.
- For role-adjusted sustained damage at equal budgets, investigate master-branch gaps above roughly 20%. Support/control branches may trade damage for measured ally protection, healing, or uptime, with that tradeoff documented.
- Barriers/heals use actual stats and real damage/healing rules, caps and cooldowns. Multiple copies of the same support effect do not multiply into invulnerability. Define source/refresh/stack behavior for same-skill, different-skill and multi-player zones.
- Burst is allowed, but no instant boss kill, permanent hard-control loop, infinite Mana/resource generation, zero-cooldown loop, or new path to exceeding established mitigation/healing caps.

If existing global balance failures remain, record the baseline and distinguish new regressions. Do not weaken assertions, change unrelated base mechanics, or retune every monster merely to hide an overpowered advancement.

Prepare a reusable **requirement query** for future Transcendent Dungeons: minimum advancement stage, allowed base families, and optional required exact/lineage classes, with clear failure text. Reuse the same registry semantics and test absent/unknown IDs and combinations. This update does **not** require adding new dungeons or locking existing ones behind transcendence. Do not force players into a particular master choice by inventing new access restrictions now. The future query should be genuinely callable and tested rather than an unused comment.

## 11. Inspected integration points

These are starting points, not an exhaustive file-edit checklist. Recheck current code before implementation.

| Area | Existing files / behavior to inspect |
| --- | --- |
| Classes/database | `game/src/data/data_classes.gd`, `game/src/core/defs/class_def.gd`, `game/src/autoload/database.gd`. DB currently registers four base classes and shared base trees. |
| Persistent hero/progression | `game/src/core/hero_data.gd`, `game/src/core/progression/hero_progress.gd`, `game/src/core/progression/tree_def.gd`, `tree_state.gd`, `game/src/autoload/save_system.gd`. |
| Abilities/resources | `game/src/data/data_skills.gd`, `data_skills_ext.gd`, `data_class_rework.gd`, `data_talents.gd`, `data_talents_ext.gd`, `game/src/core/defs/skill_def.gd`, `game/src/skills/skill_runner.gd`, `class_spells.gd`, `game/src/combat/class_passives.gd`, `game/src/actors/player/player.gd`, `class_resource.gd`. |
| Equipment | `game/src/core/items/item_base_def.gd`, `equipment.gd`, `item_instance.gd`, `item_generator.gd`, `lape_trade.gd`, `game/src/data/data_special_weapons.gd`, `data_items.gd`, artisan/depth/set/relic/Ascendant data, `game/src/core/tempos/tempo_rules.gd`. |
| Sources | `game/src/loot/loot_pools.gd`, `game/src/data/data_loot_pools.gd`, `game/src/core/shops/shop.gd`, shop/crafting data and current reward paths. |
| Guild House/service | `game/src/data/data_npcs_guildhouse.gd`, `game/src/world/maps/interior.gd`, `game/src/npc/npc_services.gd`, `npc_directory.gd`, `game/src/core/dialogue/dialogue_session.gd`, Events/UIRoot service dispatch. |
| UI | `game/src/ui/windows/character_window.gd`, `skills_window.gd`, `talents_window.gd`, `game/src/ui/widgets/tree_view.gd`, `tips.gd`, saved hero/account menu, team/Showcase views. |
| Remote identity/visuals | `game/src/net/net.gd`, `net_guard.gd`, `net_avatar.gd`, `net_codec.gd`, `game/src/actors/character_visual.gd`, hero customization/material helpers. Preserve bh-035 appearance changes. |
| Official persistence | `game/src/autoload/official_service.gd`, `server/service.py`, official tests/integration probes, save import and trade validation. Base class is immutable in the server. |
| Existing checks | `game/tests/run_tests.gd` supports `-- --only=...`; relevant suites include progression, skills, items, crafting, loot, NPCs, net, net_guard, official_server, boss_set_network, bh035, and character_skills_layout. |

Add focused data/services (suggested: `data_transcendence.gd`, `class_transcendence.gd`, `class_requirements.gd`, a transcendence window, and dedicated tests) where they keep responsibility clear. Do not duplicate complete four-class systems or create twelve independent copies of the player controller.

## 12. Claude implementation stages and acceptance gates

### Stage 1 — registry, state, catch-up, grants, and persistence

Capture baseline Git status and relevant tests. Implement the registry, effective identity API, path validation, per-hero tree composition, free-rank floors, advancement operation, save load/order, and official validation. Wire a real advancement event and durable persistence flow. Keep base IDs and progression intact.

Verify all four families at levels 1, 59, 60, 61, 119, 120, 121, 179, 180, 240, and 300. Test both master choices, no skipping, no third advancement, duplicate calls, cancel, save/reload, both catch-up steps, corrupt paths, cross-family IDs, shared-tree leakage between heroes, preserved attributes/XP/equipment/quests, rank floors, respec/refund round trips, point totals, and import identity. Test official creation/import/save/reconnect and failed acknowledgment using isolated storage.

**Gate:** progression is fully testable and safe before combat/UI polish hides state errors.

### Stage 2 — all authored abilities and talents

Implement all 36 skills and 36 talents, real effects and resource interactions. Preserve base/first-stage skills and block sibling-branch allocation, grants, hotbar use, casts and passive application. Add icons through existing assets/fallback conventions and distinguish abilities clearly in the UI. Write the initial numeric balance catalogue and tune against actual scenarios.

Test animation-hit execution, rank progression including rank 25/+5, cooldown/resource payment once, missed/evaded hits, immunity, line of sight, movement limits, status behavior, damage/healing attribution, secondary-hit recursion, aura/zone stacking, skill bar full/empty, load with locked branch IDs, and cleanup on death/map change. A test that merely checks 36 IDs exist is insufficient; exercise each behavior family and every new special hook.

**Gate:** every listed skill/talent has runtime effect and accurate current/next-rank text.

### Stage 3 — equipment rules, all old gear, 36 new pieces, acquisition

Implement the central requirement model/evaluator/formatter. Audit existing gear and emit a machine-readable manifest with item ID, requirement kind/IDs, readable text, minimum level/drop level, existing wearer/Tempo constraints, and acquisition sources. Add all thirty-six bases and reachable source/recipe integration, class fit and upgrade/trade persistence.

Test a complete matrix of sixteen identities against every requirement kind and every new gear piece. Include Knight family inheritance, Royal Guard lineage, Grand Paladin-only refusal for Dark General, shared gear, multiple families, unknown IDs, Tempos, Unbound, direct equip/swap, load repair, full bag, recovery save/reload, crafting, enchanting, sockets, trading, Showcase, deterministic loot bands, and existing set/Ascendant bonuses. Assert that every equipment base has explicit correct requirement presentation. Sample seeded generation so item source reachability is proven.

**Gate:** restrictions are enforced centrally, old equipment is preserved, and new gear is obtainable now.

### Stage 4 — Grand Master, UI, class themes, multiplayer presentation

Finish the reachable NPC/service, preview/choice/confirmation flow, Skills/Talents pages, effective names, reminders, and consistent requirement labels. Implement each theme and all eight master glows locally/remotely. Complete profile/appearance/official refresh and coordinated protocol compatibility.

Run at least two real clients for both custom and official-account multiplayer, and exercise host/member/late join/reconnect/map change/world handoff. Show a base hero, first-stage hero and both master choices of a family. Advance while a peer is already watching and verify the label/theme/glow update after accepted persistence. Include remote appearance rebuild after equipping gear, ordinary profile updates, failed save, different hero login, stealth, death, revive, quality toggle and cleanup. Test malformed profile/class claims; no arbitrary labels/effects and no stale master glow on a non-master hero.

Capture actual client views showing the updated class in its **existing position beneath** the player name and subtle master effects. A local-only screenshot is not proof of multiplayer replication. Capture every class theme in an in-engine gallery plus representative solo/remote normal-game scenes; do not claim gallery renders prove network behavior.

**Gate:** visible identity follows the actual selected/saved class in real multiplayer, and the UI is readable on the required layouts.

### Stage 5 — balance, regressions, visual/performance evidence, handoff

Run relevant full suites and account-service/integration checks using the current installed engine/toolchain. Do not reuse the old hardcoded engine path in `tools/run_tests.sh` blindly. Scan complete process logs for parse/runtime errors in addition to test summaries. Keep new evidence isolated and copy existing reports if the harness overwrites them. Avoid concurrent Godot imports/exports touching the same project cache.

Measure low/default graphics with a representative twelve-player/all-master visual scenario, including frame time and new glow draw/particle cost relative to the same scene without effects. Record engine, renderer, resolution, settings, hardware, scenario, repeats, and median/p95. If actual Android device access is unavailable, record phone-layout testing and the remaining device checks accurately; do not equate desktop touch mode with Android performance.

Deliver in `output/class-transcendence/`:

- `CLAUDE_REPORT.md`: implementation status per required area, changed-file summary, exact commands/results, baseline vs new failures, unresolved blockers, assumptions/tuning decisions, and absolute evidence paths.
- `class_catalogue.json` or equivalent: all sixteen identities, lineage, themes, all new skills/talents with final formulas/costs/caps/ranks and gear.
- `gear_requirements.json`: full equipment audit, all thirty-six new pieces and source IDs.
- `balance.csv`/report: comparable builds at the required levels, damage/control/support/sustain results, worst-case proc/stack results, and branch tradeoffs.
- Focused test results, service/integration logs, old-save fixture round trips, screenshots for advancement/skills/talents/equipment and **both clients'** floating labels/glows.
- Performance measurements and a concise remaining real-device checklist where applicable.

Update player-facing documentation/changelog with actual completed behavior. Finish with a concrete reviewable implementation and honest evidence. Do not mark the milestone complete if any class is a placeholder, master skills cannot be used, new gear has no source, old high-level saves cannot catch up, requirements are only tooltip text, or remote floating classes/glows do not work.

## 13. Final acceptance checklist

- [ ] Four starting classes and twelve new identities; Hunter displayed with `ranger` compatibility retained.
- [ ] Guild House Grand Master available without guild membership; advancements at 60/120 only; old level-121 saves can complete both immediately.
- [ ] Three functional active skills and three functional talents per advancement; six of each along a chosen master path; previous content retained.
- [ ] Earned rank floors and paid ranks remain correct through respec, refunds, saves, failures and retries; no duplicated rewards.
- [ ] All equipment has readable class requirements; family/lineage/exact/shared rules actually enforce equip and load behavior; Tempo/Unbound semantics retained.
- [ ] Thirty-six new gear bases with real reachable sources, proper drop/level bands and branch restrictions.
- [ ] Effective class in Character, Skills/Talents, saves/accounts, Team and Showcase; readable desktop/touch layouts.
- [ ] Other players see the current class in its existing position beneath the player name; all twelve distinct transcendence themes; all eight subtle master glows work remotely and without bloom.
- [ ] Official save/class validation, metadata refresh, custom/official multiplayer, late join/reconnect/map/host changes and coordinated version compatibility tested.
- [ ] Existing gear/dyes/set effects, combat rules, world progress, saves and multiplayer work preserved; no new loops, lost items, shared-tree leakage or stale effects.
- [ ] Balance and performance measured; log errors reviewed; baseline failures separated; complete evidence handed back for review.

**This is a major progression milestone. Complete the whole feature and its verification before declaring it finished.**
