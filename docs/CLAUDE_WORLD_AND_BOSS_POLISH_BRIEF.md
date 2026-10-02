# Town, creature, boss, item and rank polish brief

Prepared by Codex on 3 October 2026 for Claude Code, the primary programmer.

## Handoff prompt

Read this file after your current beta stability and performance milestone. Finish
the current checks and record their results first. The user has now requested more
presentable towns, consistent themes, free 3D creature downloads with rigging, and
distinct boss encounters with the variety and teamwork of raids. The user also
explicitly requests an overhaul of equipment stats and item drops, sufficient
crafting/enchanting materials, and simple optional rank-up guidance. These item
and guidance changes are required beta work, not optional later ideas. Implement
the milestone below, then expand only after its evidence passes review.
Keep the existing beta release, multiplayer, hosting, EXE and APK objectives.

Codex created only this additional brief during your current run. It has not
changed your gameplay code or run competing imports, benchmarks or exports.

Read the applicable repository instructions and current lore before changing
content. Preserve the author's canon, quest pacing, promotion rules, existing
characters and saves. All new mechanics below are proposals, not claims that they
already work. Inspect the current implementations before choosing changes.
Use readable, plain interface labels. Save genuine progress screenshots and
report measured results, unresolved issues and exact output paths.

## Order and first milestone

1. Finish current stability/network/performance work and establish a clean
   measured candidate. Existing baseline dense combat was well below the desired
   frame rate on a Ryzen 7 5700X / RTX 4060. PC touch mode does not certify Android.
2. Audit and overhaul item stats, monster/dungeon loot pools and crafting material
   availability as specified below. Validate generated gear and actual pickup,
   refinement, crafting and enchanting paths, not just authored tables.
3. Add the optional next-rank checklist and simple step-by-step guidance below.
4. Improve one connected Malasugue route: arrival terrace, fountain plaza, market,
   forge and south gate. Capture identical before/after gameplay camera views.
5. Download at least 20 distinct free town/interior object models as specified
   below, curate a matching set, and integrate suitable objects into the town route
   and one existing interior. Keep unused source files outside runtime exports.
6. Select three creature candidates with different silhouettes, rigs and combat
   roles. Download free source models, preserve suitable existing animations,
   rig or repair only where needed, and integrate them through existing enemy IDs
   where possible. Add a new enemy ID only for a genuinely distinct approved role.
7. Improve the Hollow Warden encounter using its existing arena/pillar design,
   then Verdigast as a contrasting arena-control encounter. Demonstrate the new
   decisions in solo and cooperative play before expanding the boss roster.
8. Repeat the relevant graphics, gameplay, network and save checks. Provide a
   reviewable change summary and screenshots before the final release exports.

Keep larger content additions in a separate backlog. Do not replace the whole
world, rebalance all classes, rename canon characters or turn every fight into
the same set of raid mechanics. Keep a reversible path for asset substitutions.
The newly authorized item-stat and loot overhaul supersedes any earlier request
to limit this stage to presentation or avoid a broad item balance pass.

## Required equipment-stat overhaul

User report: armor can receive four resistance bonuses and become excessively
strong, while some weapons have weak or irrelevant stats/effects. Replace
unconstrained combinations with coherent equipment identities and a documented
power budget by slot, item level and rarity. Keep useful variation and hybrid
builds; do not solve this by making every item identical or forcing only the
player's current class to be useful.

Read-only findings from the current working tree, not a completed runtime audit:

- ItemGenerator already has category, item-level, rarity and class-fit checks.
  Review and extend those rather than adding a second independent generator.
- Its affix exclusion uses individual groups; DataItems gives res_fire, res_ice
  and the other elements different groups. That prevents duplicate Fire rolls
  but does not prevent four different resistances or all-resistance stacking.
- The generator currently allows several affixes at higher rarities. Affix count
  alone does not express the total strength or coherence of a piece.

Implement and document:

- Meaningful base stats: weapon damage range, attack speed, reach, scaling and
  requirements should fit the weapon type; armor protection, weight and utility
  should fit its slot and armor identity. Test resulting combat performance,
  not merely the tooltip's summed numbers.
- Eligible effect families for weapon/armor/accessory roles, with compatibility,
  exclusion and shared strength limits. A slow heavy weapon and a fast weapon
  need different damage-per-hit expectations; caster effects must actually apply
  to the supported spells, and triggered powers must be able to trigger.
- A bounded amount of randomness within an authored role. Each generated weapon
  should have useful baseline offensive value and supporting modifiers; avoid
  filling its enhancement allowance with unrelated stats. Avoid requiring that
  every higher-rarity item dominates every lower-rarity specialist item.
- For ordinary generated armor, allow at most two distinct random elemental
  resistance effects as the starting rule. Make all-resistance mutually exclusive
  with random individual elemental-resistance effects. Account for base implicits,
  license bonuses, sockets, enchantments, set bonuses and powers in the combined
  defensive budget; do not bypass the rule by adding four equivalent effects
  through different systems. Any authored unique exception needs an explicit
  trade-off and tested total strength. Four random resistance bonuses must no
  longer be an ordinary armor roll.
- Level/rarity ranges, offensive and defensive budgets, stacking order and caps
  that are validated across complete equipment sets. Check actual mitigation and
  time-to-kill against representative enemies and bosses, including multiple
  elements, penetration, status effects and converted damage.
- Consistent rules for dropped, crafted, enchanted, tempered, socketed and reward
  equipment. Reforging and enchanting must not escape the same exclusions/budgets.
  Keep comparisons and tooltips consistent with calculated combat stats.
- A versioned migration for existing items if their invalid combinations change.
  Back up sample saves; preserve item identity, ownership, sockets, upgrade history
  and legitimate crafted investment. Use deterministic corrections, not a fresh
  random reroll on every load. Clearly record intentional balance reductions;
  verify save/reload, trading and migration run exactly once.

Deliver a short balance sheet with representative before/after weapon and armor
examples, then seeded sample distributions across slots, level bands and rarities.
Test forbidden combinations, actual stat application, extreme full-set stacking,
upgrade paths and legacy items. Do not change unrelated class mechanics solely to
make old fixtures pass.

## Required dungeon/monster loot pools and material supply

Define data-driven pools with explicit composition and precedence:

| Pool | Purpose |
| --- | --- |
| Per monster | Believable parts, carried/salvaged equipment, relevant materials and required quest items. Metal-bearing enemies can yield scrap; animals primarily yield biological materials. |
| Dungeon theme/type | A reusable theme identity for ordinary drops and supplies: fungal, drowned, forge, rime, astral and other existing themes. |
| Individual dungeon | Specific additions, weighting and signature rewards that distinguish one dungeon from others sharing a theme. |
| Boss/chest/completion | Authored trophies, appropriate equipment and reliable progression supplies, with explicit repeat-clear rules. |

Reuse the existing per-monster EnemyDef.loot entries and current dungeon materials,
orb preferences and boss sets where appropriate. The generic equipment path
currently selects from ItemGenerator.random_base; audit its integration with
monster and dungeon context. Define whether each pool adds, inherits, replaces
or excludes entries so theme composition cannot double rewards or erase required
monster items. Apply level, difficulty and usable-equipment rules deliberately;
avoid an empty pool silently becoming an unrelated global random drop.

Every existing monster and dungeon needs a resolved pool or documented inheritance.
Validate item IDs, recipe IDs, weights, probabilities, stack counts, level gates
and source reachability. Preserve themed special drops and authored requirements.
Quest items need a bounded, appropriate acquisition path while the quest is active;
irrelevant quest drops should not permanently clutter the player's bag.

User reports never seeing Iron or other metal materials. Current source findings:

- iron_shard exists as Iron Shard in DataItems and appears in several enemy tables.
- DataCrafting refines five Iron Shards into one Steel Ingot at a forge, with a
  four-gold fee. Steel is authored as refined stock, not a universal monster drop.
- AutoLootRules.item_reason currently compares min_rarity with every item's rarity
  after its quest/unique exceptions. Common materials can therefore be rejected
  by a filter intended to collect better equipment. This is a candidate cause,
  not proof that it caused the user's missing drops.

Double-check and fix the full chain: valid registered item definition -> intended
monster spawn -> kill owner -> drop roll -> world drop -> visible label/filter ->
manual/automatic pickup -> stack placement -> save/reload -> recipe consumption.
Check multiplayer remote kills, owner changes and full bags too. Equipment rarity
filters should not silently exclude enabled material categories. Keep explicit
ingredient exclusions working and make filter behavior understandable.

Build a recipe-to-sources coverage table for all crafting, enchanting, tempering
and socketing costs. Flag ingredients with no reachable source, inappropriate
level gates or supply too low for their normal use. Check refinement ratios,
recipe unlock timing, gold costs, salvage output and consumable demand together.
Verify salvage cannot create an infinite craft/sell/material loop.

Provide sufficient primary monster/dungeon material drops and intentional
fallbacks where appropriate, such as salvage, gatherable resources or limited
merchant supply. Do not make every creature drop every metal. Early crafting
should be achievable during normal early play; document a reasonable time-to-first
craft and ongoing upgrade targets, then measure them through representative routes.
Report units per clear and estimated time for representative recipes. Required
materials should have reliable quantities or bounded bad-luck protection where
pure randomness would stall progression. Keep loot counts/performance bounded.

In crafting tooltips, show the existing material name, owned/required amount,
concise acquisition hints and any refinement step. Example: "Steel Ingot — forge
from 5 Iron Shards." Add source hints based on actual resolved pools, not guesses.
Verify monsters visibly drop Iron Shards and that a player can collect enough to
refine, craft and enchant a useful item through the normal interface.

## Required simple rank-up guidance

Provide optional guidance for the next rank only. The user wants step-by-step
instructions and a checklist that can be minimized or hidden conveniently.
Existing code already exposes next-promotion/missing-requirement functions and
character-window promotion text. Improve this flow using a single shared source
for eligibility and progress; do not maintain a separate UI-only rule set.

Suggested flow:

1. Character screen and an appropriate guild/story interaction offer "Rank Up".
   Show current rank, next rank and one immediate next action in plain language.
2. "Track Rank Up" opens an optional compact checklist. Show complete/incomplete
   state and meaningful counts, with short destination/NPC hints where known.
   Fold completed requirements and expose details on request.
3. "Minimize" keeps one short progress line; "Hide" removes the tracker. A visible
   Character-screen action restores it. Remember the player's choice per hero.
4. Update on relevant quest/level/inventory/guild events, not a costly per-frame
   rebuild. When eligible, say either "Ready to rank up" with the correct action,
   or explain that the promotion is automatic if that is the actual approved rule.
   Never instruct a player to visit an NPC or pay a fee that the game does not need.

Support desktop and touch safe areas; avoid covering combat warnings, minimap or
buttons. Do not show the full E-through-SSS ladder or spoil future story objectives
in the default tracker. Unranked/no-guild players need a truthful first step;
maximum-rank players should not see a broken or empty checklist.

Preserve canon: Paul David tells the heroes' story in Quest 3 and the player ranks
up after that quest. Only the author assigns further promotion quests. Current
tables include provisional later deeds, levels, fees and achievements; distinguish
those from approved rules and flag conflicts for the user. This UI request does
not authorize inventing new promotion quests or making provisional tasks canon.
Do not change Quest 8 Kethrax pacing to match an old rank table.

Test the eligibility/checklist agreement for missing, partial and completed
requirements; hidden/minimized/restored state; save/reload; guild changes; legacy
saves; story-triggered promotion; and any multiplayer progress delivery. Capture
the expanded, minimized, hidden and ready states on desktop and touch layouts.

## Town identity and layout

| Place | Existing identity | Proposed presentation work |
| --- | --- | --- |
| Malasugue | Walled fishing and hero town on Salmonan's west-coast cliff plateau | Weathered timber, pale stone, repaired fishing nets, marlin/swordfish details, warm hearth light and clear coastal views. Preserve the burnt house and shrine as story landmarks. |
| Olivar | Walled town trading on Stillwater Lake | Barges, dock equipment, merchant awnings, organized stalls, lake reflections used sparingly, a distinct lake terrace and a recognizable founder's plaza. |
| Wyman Outpost | Shared hero camp above Reedwater Marsh | Practical tents, repaired stockade, workbench, training yard, watchtower and a central communal bonfire. Keep the marsh visible from the overlook. |

Start with a small shared art guide: scale, roof and wall shapes, a limited palette,
surface roughness, trim, prop density and night lighting. Match new assets to the
game's current heroes and environments. A model being free does not make it a good
visual fit. Avoid mixing cartoon creatures with detailed heroes without adapting
their materials and proportions.

Design from the actual gameplay camera and mobile aspect ratios:

- Make the fountain, terrace and guild entrances recognizable without relying on
  minimap labels. Paths should visibly lead to services and exits.
- Keep a short, clear route between commonly used services. Audit collisions,
  stairs, doorways, interaction reach, pathfinding and party gathering spaces.
- Fade obstructing roofs/trees appropriately. Keep dialogue speakers and service
  signs visible; make interactable entrances distinct from decorative doors.
- Use ground patterns and silhouettes to divide districts. Add benches, laundry,
  net-mending and smithing details where they explain daily life.
- Give a few NPCs inexpensive idle activities or short predictable routes.
  Background life should not require dozens of fully simulated physical actors.
- Use a small number of important shadowed lights, shared materials and batched
  repeated props where suitable. Profile batching rather than assuming it helps.
- Give each town ambient audio and music appropriate to its identity. Use sound
  zones and restrained overlapping voices, with a separate ambience volume.
- Let existing quest flags change a few visible details: repaired gate, returned
  trader, shrine token or a cleared notice. Do not add unauthorized story outcomes
  or promotion quests. Preserve the author's level-40+ Quest 8 Kethrax pacing.

## At least 20 downloaded town/interior objects

Additional explicit user requirement: download at least 20 distinct free 3D
objects/assets for town and interior design. A source pack containing 20 or more
different suitable models can fulfill the download requirement; twenty copies,
recolors, empty files or references to download pages do not. Record the exact
individual models actually downloaded. This prop count is separate from the three
creature candidates.

Use the existing game's proportions and material style to choose the set. Target
24 categories below to allow substitutions when a model does not fit. These are
selection requests, not claims that a particular pack contains each item:

| Use | Requested distinct models |
| --- | --- |
| Fishing town | Fish crate, fishing net, rope coil, mooring post, handcart, market stall |
| Shared streets | Bench, signboard, barrel, wooden crate, planter, lantern fixture |
| Tavern/home interior | Table, chair, bed, cabinet, shelf, cooking pot |
| Forge/guild interior | Anvil, tool rack, workbench, weapon rack, bookcase, notice board |

Choose at least 20 suitable downloaded models across these uses. Review their
actual licenses and list each model's source pack, source URL, license, local path,
hash, dimensions, material count and intended placement. Prefer CC0 sources for
this pass. Keep original archives and license files. Create source-to-runtime
records so a model can be replaced without losing its provenance.

Present a preview sheet of the complete downloaded selection and screenshot the
curated objects placed in Malasugue and one existing interior. Integrate those that
pass visual/import/performance checks; explicitly explain unused or substituted
models rather than filling the level with clutter to hit the count. Audit scale,
collision, interaction routes, roof/camera obstruction, texture memory, repeated
materials and draw calls. Do not add a light or independent physics body to every
decorative object. Preserve the existing interactive station scripts and saves.

## Free creatures: download, inspect, rig and integrate

Verified source candidates as of this brief:

- Quaternius Ultimate Monsters: 50 animated models, listed CC0, with Blend, FBX,
  OBJ and glTF options: https://quaternius.com/packs/ultimatemonsters.html
- Quaternius Easy Enemy Pack: five animated enemies, listed CC0:
  https://quaternius.com/packs/easyenemy.html
- Kenney Fantasy Town Kit: 160 files, listed CC0; optional modular props only if
  their style fits: https://kenney.nl/assets/fantasy-town-kit
- Quaternius Ultimate Furniture Pack: 20 models, listed CC0, including furniture
  essentials; review individual models for the current interior style:
  https://quaternius.com/packs/ultimatefurniture.html
- Adobe Mixamo: its FAQ permits royalty-free game use, but its auto-rigger and
  library support bipedal humanoids only:
  https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html

Use official download links. Inspect the downloaded pack's actual license, files
and animation content; these are candidate sources, not an admission receipt.
Choose CC0 for this initial free-model pass. Record source URL, author, pack/model
name, download date, license file, SHA-256 digest and any modifications. Keep a
source archive outside engine imports and only include used runtime assets in
exports. Do not download paywalled assets or ripped characters from other games.

Inspect current project creatures before selecting replacements. Start with
three compatible candidates from the actual downloaded files. Useful directions
include a readable shelled reef crawler, a quadruped rootback boar, and a distinct
fungal caster or brute. These roles already exist in the game's data; avoid
creating duplicate roster entries merely for a new mesh. If no compatible free
candidate exists, record that gap and retain the existing creature.

For each selected model:

1. Inspect topology, material count, texture sizes, skeleton, animation names,
   dimensions and license. Preserve originals and work on separate copies.
2. Prefer a supplied functioning rig. Use Blender to clean scale/axes, repair
   weights and add missing poses. Use Mixamo only for a suitable humanoid and an
   already available authorized account; it will not solve quadruped or spider
   rigs. Never describe a download as successfully rigged without inspection.
3. Supply idle, movement, anticipation, attack, recovery, hit and death states
   appropriate to the creature. Different attacks need distinguishable poses;
   reusing one generic swing weakens readable combat.
4. Keep movement authority in the existing gameplay/network implementation.
   Validate feet, root motion, sockets, weapon attachments, animation hit timing,
   bounds, shadow, collider and nav dimensions in Godot.
5. Create distance reductions appropriate to the current renderer: mesh detail,
   animation update frequency and shadow distance. Lower graphics must preserve
   enemy shape, attack warnings and target selection.
6. Capture a neutral preview, an animation contact sheet and an in-game close/far
   screenshot. Test several simultaneous instances with the actual renderer.

Starting asset budgets are provisional investigation targets: common creatures
around 3,000-8,000 visible triangles, 1-2 materials and 512-1024 textures; bosses
may need more detail. Measure actual draw calls, animation/physics work and memory
before accepting exceptions. A triangle budget alone does not guarantee speed.
Avoid giving every creature a costly always-active physical bone simulation.

Combat roles should be distinguishable before a health bar is read: low/wide
shelled blocker, fast quadruped charger, tall caster, heavy slow brute. Introduce
their mechanics individually before combining them in later groups. New concepts
for a later pass include a burrower with a visible emergence trail, a flanker that
signals its pounce, and a support creature with a clearly breakable tether.

## Boss encounters with distinct decisions

These are proposed extensions to named existing encounters. Reuse current attacks
where they support the identity. Verify the existing Warden charge/pillar behavior
before expanding it; several dungeon bosses already have named HP phases.

| Boss | Main player decision | Proposed signature sequence |
| --- | --- | --- |
| Morthar, the Hollow Warden | Position and bait | Bait a clearly aimed charge into an intact pillar, exploit the resulting recovery, then move as broken pillars reduce available cover. Keep a viable fallback when pillars are exhausted. |
| Verdigast, the Rot Mother | Preserve safe ground and choose targets | Rot patches consume selected arena sections; destroy a visibly growing bud to reopen ground before its bloom. Later phases combine the existing ring warning with a bounded number of buds. |
| Ossric Vael, the Drowned Bell | Move between safe heights | Bell pulses announce a tide change. Reach a clearly marked raised section, then return for a vulnerable window. Use a small set of reusable hazard volumes instead of simulated flood physics. |
| Brakka Durnhelm, the Forgemaster | Redirect heat and use an opening | Telegraph which forge lane will heat; bait a hammer strike toward an exposed coolant fixture to crack armor. Later sequences change lane order without removing escape routes. |
| Skaldra, the Winter Crown | Preserve useful cover | Ice markers warn of an approaching sweeping attack. Keep a marked ice pillar intact for cover, then use its broken shards to expose a recovery opportunity. Frost effects must leave warnings visible. |
| The Astrarch | Read rotation and control space | Orbiting machinery predicts the next beam lane. Disable an exposed lens during its recovery to create a temporary safe sector; later phases change rotation direction after a clear cue. |

For later raid encounters, consider complementary paired bosses, a ritual that
can be interrupted through either combat or arena interaction, or a moving boss
whose weak point is reachable during a clearly signaled route. These remain
proposals. Preserve Kethrax's commander role and campaign placement.

Each boss should have two or three signature mechanics, recognizable attack
families and meaningful recovery windows. A phase change should alter positioning
or priorities. Avoid difficulty consisting only of more HP, extra damage,
permanent adds or increasingly long invulnerability.

Variation should remain learnable. Select among compatible sequences with
cooldowns and a bounded repetition rule. Validate combinations so a ring attack,
charge and ground hazard cannot remove every escape path. Preserve enough lead
time for the supported movement speed, touch controls and expected latency.
Teach each signature mechanic in an easier earlier encounter where appropriate.

## Raid usability and multiplayer correctness

- Keep mechanics completable solo. Cooperative roles can be useful without
  requiring specific classes or voice chat. Participation requirements must
  account for connected, living players and disconnects, not the server's
  twelve-player capacity. Prefer adjusting between attempts, not abrupt changes
  during an active attack.
- Use short objective text, recognizable shapes, optional party markers and
  distinct sounds. Never encode danger only by color. Reduce decorative effects
  before reducing warning visibility. Provide camera shake and flash controls.
- Allow a clear ready check and quick retry at an appropriate checkpoint. State
  why a wipe happened and what the player can try next. Avoid long repeated walks
  or unskippable introductions during boss learning.
- Define ownership of phase changes, timers, arena fixtures, summons and damage.
  The current map-owner simulation needs explicit handoff and late-join snapshots.
  Hosting the coordinator off the PC does not itself make combat server-authoritative.
- Synchronize attack identity, phase, warning start, impact time, target and
  cancellation. Visual interpolation must not create an extra damage event.
  Verify late joins, phase transitions, owner disconnect, simultaneous kills,
  wiped parties, arena exit/re-entry and reconnect during reward delivery.
- Keep rewards idempotent and saves compatible. A disconnect or ownership change
  must not duplicate boss loot, reopen a claimed chest or consume a quest twice.
- Bound summons, hazards, corpses and effects; guarantee cleanup on death, reset,
  map exit and owner handoff. Reuse lightweight visual effects where suitable.

## Additional polish to factor in

Beta priorities:

- First-session onboarding: movement, camera, dodge, healing, first equipment,
  first service and first party join. Keep each instruction short and contextual.
- Combat clarity: correct hitboxes/timing, hit reactions, interrupt rules, clear
  target selection and readable status icons; support both melee and ranged builds.
- Inventory: readable tooltips, item comparison, favorite/lock, loot filters,
  controller/touch actions and safe handling of a full bag. Verify current features
  before adding equivalents. Test selling and crafting against disconnects.
- Accessibility: adjustable UI/text size, touch safe areas, control remapping,
  independent audio channels, effects intensity and reduced motion. Keep graphics
  quality independent from the selected input scheme.
- Reliability: old-save migration, graceful offline/reconnect paths, a bounded
  crash/restart recovery flow, server backup restore drills and useful network
  errors. Test one-handed screen interactions and Android suspend/resume.
- Community beta feedback: visible build/protocol version and an easy way to
  copy a redacted diagnostic summary. Explain where to report issues; do not send
  player data or create public posts automatically.
- Release polish: consistent icons, no missing textures/T-poses, correct APK
  signing/version policy, installer/export smoke checks, concise player setup
  instructions and clear known-issue notes.

Later ideas after stability: a bestiary that records learned tells, training
encounters, optional exploration discoveries, town reactions to existing quests,
boss-specific cosmetic trophies and a small set of curated encounter variants.
Avoid adding a new progression currency, daily chores or an entire crafting layer
for this beta unless the user separately chooses that scope.

## Evidence and completion criteria

Store this stage's captures and metrics under output/world-polish-20261003/ with
revision, scenario, renderer, resolution, input mode and settings recorded.
Screenshots must be captured from actual candidate gameplay, not only a modeler.
Provide:

- Matching town route views on desktop and touch layouts; collision/pathfinding
  walkthrough results, service interaction checks and camera occlusion captures.
- A manifest proving at least 20 distinct downloaded town/interior models, with
  source/license records, a complete selection preview and in-game placement views.
- Gear balance/distribution results, coherent before/after item examples and
  versioned migration evidence for sample legacy equipment.
- Resolved monster/theme/dungeon pools and recipe-source coverage; measured
  material supply and actual Iron Shard pickup -> Steel Ingot -> craft/enchant
  walkthroughs, including enabled-material filters and multiplayer cases.
- Next-rank checklist captures in expanded, minimized, hidden/restored and ready
  states; matching eligibility results and preservation of approved story rules.
- Three creature source/license records, import/rig inspection results and the
  neutral, animation and gameplay captures described above.
- Two boss encounters showing anticipation, mechanic response, recovery, later
  phase and wipe/reset, with solo and at least two real connected clients.
- Identical baseline/candidate town, ordinary combat and dense combat scenarios;
  median/p95/p99 frame time, draw calls, memory, actor counts and loading spikes.
- A prolonged transition/combat loop showing memory reaches a stable range and
  repeated boss attempts leave no accumulating hazards, timers or actors.
- Relevant regression and networking tests, including lifecycle/log errors, not
  only a printed PASS line. Fix failed checks or report their exact limitations.

Targets remain 60 FPS at 720p/low on a specified low-end PC and sustained 30 FPS
on a specified low-end Android device. Frame budgets are approximately 16.7 ms
and 33.3 ms respectively; inspect tail spikes and thermal behavior as well as
averages. If those devices are unavailable, state the tested hardware and leave
device qualification open. A PC capture in mobile mode is an emulator-style UI
check, not evidence of Android performance.

Report what was changed, what was only proposed, what was measured, the screenshots
and artifact paths, and any blocker to the beta release. Continue the final push
and EXE/APK release work through the coordinated release process after this
candidate is reviewed and passes the required checks.
