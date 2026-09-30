# Beyond Heroes - version-by-version changelog

Prepared 29 September 2026. Versions here are the repository's BH development update numbers, not invented release tags. This record covers the two latest earlier Git updates (BH-016 and BH-017), the continued BH-018 and BH-019 work, and the BH-020 completion fixes. Earlier history is outside this document's scope.

## BH-025 - Music system, recorded themes and weapon sounds

Prepared 30 September 2026.

- The seven recorded themes are in the game. **main_theme** is the default: the main menu, the towns, the roads, and any map without music of its own. Dungeons play dungeon_theme; Emberforge Depths plays fire_dungeon_theme; Rimeglass Barrow and Prismdeep Geode play ice_dungeon_theme.
- Music now follows the fight. The battle theme takes over while monsters are fighting the hero in open country (and for a dungeon's champion), and lets go six seconds after the last of them. The boss theme starts when a boss sees the hero, not at the door of its floor. The road's music carries on from where it stopped.
- Paul David speaks of Aljay and Roydo under **aljay_theme**: it starts when he sees the shard, plays through his tale and holds until the conversation ends. The chain breaking on the Black Spire plays it too.
- Music starts at 60 % and keeps whatever the player sets in Settings > Audio. New setting: Battle Music (on by default). The seven recordings are levelled against each other, the pause menu muffles the music, and three new stingers play when a boss sees the hero, when a boss falls and when the hero falls.
- Recorded sounds: sword, axe and hammer hits, the blade swing, bow shots, staff and wand attacks (and their strong attack), Cleave, Firebolt, Meteor Strike, Blizzard and Chain Lightning. Each was cut to the sound itself, so a blow sounds on the frame it lands.
- New sounds made for the weapons the pack has none for (greatsword, great axe, dagger, spear, claw, knuckles, crossbow, staff and wand bolts), and for five the game asked for and never had: the low-health heartbeat, buying, crafting, gathering and holy casts.
- The four synthesised tracks the recordings replaced are out of the build (80 MB of WAV for 25 MB of MP3).

Sources: docs/MUSIC.md, game/tests/unit/test_bh025.gd, work/lemondev/bh-025/evidence.

## BH-024 - Leggings, the complete worn wardrobe, Unbound items

Prepared 30 September 2026.

- New equipment slot: **Leggings**, between Armor and the gloves (14 slots). Leggings roll the armour enchantments plus Evasion and Knockback Resistance, carry Mythical, Legendary, Aether and relic powers, take three faction licences and socket crystals, and weigh 1.6 (cloth) to 9 (plate). Old saves load with the slot empty. Multiplayer protocol advanced to 11.
- 34 unique leggings: five for each class from level 1 to 30 (Knight plate, Mage silk, Ranger hide, Shadowblade dark leather), a leg piece for each of the four depth groups (level 44), Aether Guardian Cuisses and Starbound Sage Leggings (both sets now six pieces, with a new six-piece bonus), and eight named uniques (Rimewalkers, Windswift, Oathbound, Echoing Bastion, Stillwater, Bloodrunner, Stormstriders, Riftwalker). Every class starts in a pair. See docs/LEGGINGS.md.
- Each of the fifteen boss collections gained its **Legguards** (202 pieces in all; 14 per collection, 13 for two-handed ones): class-shaped thigh regalia in the set's palette and emblem.
- Merchants: Brannoc, Seris, Taicho's Arms Exchange, Stonehand's Field Kit and the Hooded Stranger stock leggings; Brannoc and Seris also sell the set leggings after the Catacombs ritual and a level-28 pair; the Stranger sells Windswift after the Warden falls. Crafters can make leggings.
- Inventory and Tempo paper dolls: clothing down the left (helm, inner garment, armour, leggings, glove, boot), jewellery down the right, with an engraved trousers glyph for the empty slot.
- The hero's wardrobe is complete (the unfinished part of BH-023): every armour, inner garment, helm, glove, boot, ring, amulet and charm now has its own model fitted to the hero body (98 worn pieces), so a mage no longer appears in a knight's hauberk and iron helm. Body garments stop at the hips; the legs are covered by leggings, by plain breeches under a shirt or coat, or by a set-coloured under-layer beneath boss Legguards. Belts, thigh plates, knee cops and ankle cuffs are left off where a shirt, skirt, robe or boot covers them. Worn plate armour uses a less mirror-like finish so it no longer reads as black at night.
- Unbound items: a variant with no level, attribute or rank requirement. The `alj` code gives every Legendary special weapon as an Unbound variant; the special weapons themselves are waiting for their models (models/special_weapon/ was not in the repository), see docs/SPECIAL_WEAPONS.md.
- Fixed test_bh023's save call, which stopped the whole headless test run under Godot 4.7.2.

Sources: work/lemondev/bh-024/handoff.md, docs/LEGGINGS.md, game/tests/unit/test_bh024.gd.

## BH-022 - Socket visuals, infused names, waypoints, Mythic and Eternal Tempos, rebuilt boss collections

Prepared 30 September 2026.

- Socketed equipment shows its sockets on item cells, equipment slots and tooltips: bronze bezels, each holding its crystal cut by grade. Pieces holding crystals glow in their blended colour, and held weapons shed motes of it.
- Equipment is named after its crystals: 32 single-family names in four tiers, all 28 hybrid pairs ("of the Nova Blast"), Grand and Eternal forms, third-family epithets and Fourfold / Prismatic forms. See docs/CRYSTAL_NAMES.md.
- Waypoint shrines now stand at the South Gate fork and Old Mill Crossroads, so every safe haven on the roads is on the waypoint network. They show on the minimap, world map and route planner.
- From level 25 the Mythic renowned spirits replace the Renowned at the Shrine of the Fallen and in 5-star summons; from level 45 the Eternal replace the Mythic. Twenty new spirits with portraits (shrine) and a unique skill each, carrying 85% / 95% of the hero's strength, costing 45,000-110,000 and 180,000-450,000 gold. Spirits already bound keep their tier. Mythic and Eternal spirits burn in their tier's colour in the world.
- All fifteen boss collections were rebuilt as fitted, textured regalia with set crests and emblems; the seven shields and fifteen signature weapons use the same textured palettes. New icons for all 187 pieces. Showcase PDF: output/pdf/Beyond-Heroes-Boss-Collections.pdf.

Sources: work/lemondev/bh-022/handoff.md.

## BH-016 - Skills, Guild House and player trading

Git commit: 4f0b64b784ba869e14ddc99cc87859a3503fca03 (29 September 2026).

- All skill and talent nodes can reach level 25. Effects up to the former cap retain their old values; additional levels use a taper of 0.5 normal ranks, or 0.1 for single-rank abilities and keystones. Tooltips, tree displays and saved ranks support the new cap. The character level cap and point income remain unchanged.
- Added the Guild House exterior and interior in Malasugue, with steward Hollis Varnay, Swordfin clerk Bram Ostler and Lantern clerk Sabeth Wynn, guild counters, banners and two job boards. The town well and Seris were repositioned to make space.
- Guild boards show registration or transfer, membership benefits and four level-appropriate jobs. Heroes can carry up to three jobs from their guild. Objectives include combat, exploration, gathering and crafting. Handing in a completed job pays gold once, with a 5% bonus per guild tier; postings refresh as jobs are taken or completed. Job state is saved with the hero.
- Added multiplayer player trading through nearby heroes, party frames and the Multiplayer window. Offer up to ten items plus gold. Both players must accept the same offer revision; changing an offer resets acceptance. Locked, favorite and quest items are refused. Inventory capacity, ownership and funds are checked before the exchange. Closing or disconnecting cancels the trade.
- Multiplayer protocol advanced to 5. Added guild-house, job, progression and two-process trade tests, plus desktop and touch-layout captures.

Sources: work/lemondev/bh-016/handoff.md, work/lemondev/bh-016/contract.md, and the commit diff. The earlier handoff records 1,394 checks in the new BH-016 suite and successful host/client trade probes. It does not claim physical-phone testing.

## BH-017 - Merchant Rows, combat effects and companions

Git commit: 05d8219b13f565008c6b4bb80348f7d74ea2669c (29 September 2026).

- Added Merchant Row in Malasugue, Market Row in Olivar and Quartermaster Row in Wyman. Merchants, the rare dealer, three crafting stations and the Malasugue Tempo shrine use coordinated locations from a shared town table. Trade objects identify the stands; nearby nameplates identify their owners. Updated town layouts, world-map routes, dialogue and the guide.
- Added five buffs: Vigor, Keen Focus, Windstep, Titan's Might and Spirit Ward. Added five debuffs: Grievous Wound, Enfeebled, Dazzled, Sundered and Demoralized. Grievous Wound reduces healing and regeneration by 25% per stack, up to three stacks. The effects are connected to monsters, skills, five elixirs and two throwable flasks. Previously undefined Dazed and Blinded effects now have rules.
- Added status icons and item models/icons for the new consumables, with recipes and merchant stock.
- Equipment generation favors the hero's class in monster drops, chests, caches, mimics, set/unique rolls and class-aware shops. The class-hinted selection uses a 72% preference branch while allowing other equipment to appear.
- Added the single-player `quake team` command for up to three AI hero allies. Allies use class skills, follow and fight, drink potions, buy and equip improvements in town, sell replaced gear and bind a Tempo. Their gear, gold and progression are saved; defeated allies recover after 14 seconds.
- Added Enchantment at alchemy tables: rank I-III elemental runes with 20/30/40% conversion and additional bonuses. Added Fore-Tech at forges: mechanical weapon refits from +1 to +5, giving 2% weapon damage per rank plus a refit effect. Both upgrade types can coexist on a weapon and appear in crafting screens and tooltips.
- Added custom guild names and banners. Names support up to 32 characters with unsafe formatting removed; PNG/JPG/WebP images are cropped to a 2:3 banner and stored with the hero. The banner appears in the customization window, Character window and Guild House.

Sources: work/lemondev/bh-017/handoff.md and the commit diff. The earlier handoff notes that remote players' custom guild banners are not displayed, and the phone file picker had not been tested.

## BH-018 - Socketing, crystals and town redesign

Continued local update, included in the current completion release.

- Added 32 socket crystals: Ember, Aqua, Nova, Thundra, Vipera, Bloodrift, Essencerift and Aetherift, each in Fragment, Shard, Crystalline and Orbital grades. Added their models, inventory icons, grade colors, descriptions and effects.
- Crystal effects depend on the equipment: weapons, armor/shields or jewelry. Bloodrift and Essencerift fit weapons only. Aetherift adds rare effects: chain lightning after critical attacks, protection at low health, or cooldown reduction after critical hits; its Orbital jewelry form also grants a skill level.
- Added socket specialists Ysolde Marr in Malasugue, Anselm Cray in Olivar and Dagna Flint in Wyman. Their conversations explain sockets and open the service window or crystal shop.
- Added services to open sockets, close empty sockets, set a crystal for free, purge crystals while keeping the equipment, and crystallize equipment to recover its crystals. Destructive services require confirmation. Worn items update stats; socket contents persist in saves and trades.
- Maximum sockets by equipment tier: Beginner/Common 1; Basic 2; Advanced/Licensed 3; Elite 4; Master 5; Mythical/Legendary 6; Aether 7. Opening additional sockets gets more expensive as item level and socket count increase.
- Bosses always add a crystal drop. Champions/minibosses drop Fragments or Shards. Aetherift is rarer than the other families. Specialist shops carry unlimited level-gated crystals; normal base prices are 5,000 / 15,000 / 45,000 / 135,000 gold by grade, with Aetherift at three times those values. Merchant relationship modifiers can alter final prices.
- Doubled carrying capacity: base 55 to 110, Strength contribution 1.6 to 3.2, and Featherweight Draught capacity bonus 60 to 120.
- Replaced generic merchant stands with distinct medieval shop and crafting models, revised the three town quarters and removed the old freestanding signs. Updated map locations, minimap icons, dialogue and guide entries.
- Fixed elevated dungeon-gate approaches with sloped, walkable aprons. Updated related gate and town layout tests.
- Multiplayer protocol advanced to 6 so older clients cannot silently discard crystals or socket data in trades. Added an item catalogue and socket/crystal tooltips.

Sources: game/src/data/data_crystals.gd, game/src/core/items/sockets.gd, game/src/data/data_shops.gd, game/src/data/data_town_rows.gd, the working changes, and game/tests/unit/test_bh018.gd.

## BH-019 - Lape, practice dummies and shared storage

Continued local update, included in the current completion release.

- Added Lape the Ancient in Malasugue with a dedicated portrait, relic stall, dialogue and trading window. His completed character model has a black hooded robe, white beard and large staff; six townsfolk animation clips were exported and checked.
- Lape accepts up to three items for appraisal, identifies their properties and requirements, and uses more than 300 authored comments. Eligible trades offer three class-appropriate, licensed, specially crafted equipment choices. The player chooses one item or takes the appraised gold; the submitted items are exchanged only when the trade is accepted. Low-value lots can be exchanged for gold without crafted offers.
- Added practice dummies to Malasugue, Olivar and Wyman. They accept attacks without dying or fighting back, rock when hit, show damage numbers and report the last hit, largest hit, five-second damage per second and bout total. They are excluded from normal enemy targeting by companions and the minimap.
- Added the Hero's Vault, shared across the player's saved heroes on the device. It starts with 32 slots; 2,500 gold expands it to 64 and a further 8,000 gold expands it to 128. Deposits, withdrawals, upgrades and saved item data are supported. Quest items stay with their hero. Tests and captures use a separate vault file.
- Added vault and dummy models and dedicated interaction screens. Updated town placement, minimap entries, guide text and descriptions.
- Renamed four shopkeepers: Tovin to Anton, Hobb to Greggy, Corvin to Taicho, and Aldous Pell to Angkol Les. Updated their dialogue and shop names.

Sources: game/src/core/items/lape_trade.gd, game/src/core/items/hero_vault.gd, game/src/world/practice_dummy.gd, game/src/data/data_npcs_lape.gd, game/src/data/data_lape_lines.gd, and game/tests/unit/test_bh019.gd.

## BH-020 - Completion and usability fixes

Current completion update, 29 September 2026.

- Fixed the specialist conversation handoff: closing dialogue cleared the NPC before the deferred socket window could read its name and shop. The handoff now captures both first, so Buy Crystals opens the correct merchant in every town.
- Shop stock now supports click or tap as well as right-click purchases, retaining confirmation for expensive items. Opening another merchant resets Buyback and category filters so earlier selections cannot hide crystals.
- Existing shop saves now recover missing unlimited stock and add newly unlocked level-gated goods when reopened, while retaining finite stock, buyback items and purchased-special history.
- Nearby NPC, crafting, vault and practice labels render in front of world geometry. Companion labels sit higher and render above their health bars. This resolves the names cut off by shop roofs and bars in the reported view.
- Completed the remaining source-to-model exports, including Lape and updated smithy, wagon, Wyman and crafting assets.
- Corrected four town route endpoints to match relocated destinations. Updated the sanctuary population test to include Ysolde and Lape.
- Added regression coverage for the real dialogue-to-socket-window-to-shop flow at all three specialists, confirmation and gold charging, stale filters, and saved-stock recovery. Updated the visual capture to use the same dialogue and Buy Crystals path as players.

Validation and build details are recorded in work/lemondev/bh-020/handoff.md and its evidence folder. Windows and Android build outputs are provided separately from source control. The APK uses the project's existing debug signing configuration; physical-device testing is reported separately from a successful build.


## BH-021 - Forsaken Hero story and combat progression

- Completed the opening quest through Wyman, Paul David's account of Aljay and Roydo, the Weeping Causeway and Kethrax, connecting back to the Hollow Warden chapter. Added cinematic scenes, legendary models and animations, quest models, music and Class SX nameplates. Fixed duplicate introduction rewards, quest routing and delayed cutscene cleanup.
- Reworked level-6+ weapon drops, Strength attack, Intelligence/Wisdom spell power and caster weapons. Scaled enemy health and equipment armor, updated Tempos and player-facing stat comparisons, and protected reflected/percentage damage from applying spell power twice. Levels 1-5 keep their original growth budgets.
- Replaced level-and-gold promotions with cumulative story deeds, handed-in jobs, different champion victories and different dungeon clears. S/SS/SSS begin at levels 45/55/60 and require substantial achievements. Old saves reassess rank once and refund removed promotion fees while retaining gear. Multiplayer protocol is 8.
- Focused regression: 24,396 passing checks, plus additional percentage-damage checks and a rendered quest/boss/cutscene smoke test. Existing enemy behavior and starter-gear class-balance assertions remain documented limitations.

Formulas, measured damage, promotion requirements and build details: [Combat and story update](COMBAT_AND_STORY_UPDATE.md).
