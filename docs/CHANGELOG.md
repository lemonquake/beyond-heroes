# Beyond Heroes - version-by-version changelog

Prepared 29 September 2026. Versions here are the repository's BH development update numbers, not invented release tags. This record covers the two latest earlier Git updates (BH-016 and BH-017), the continued BH-018 and BH-019 work, and the BH-020 completion fixes. Earlier history is outside this document's scope.

## BH-036 - Class Transcendence - 4 October 2026

- **Twelve new classes**: every starting class advances at level 60 (Royal Guard, Tracker, Arcanist, Nightstalker) and
  chooses one of two master classes at level 120 (Dark General or Grand Paladin, Wildwarden or Starstrider, Archmage or
  Void Sovereign, Phantom Reaper or Blood Sovereign). Grand Master Edran Vale in any Guild House teaches it; no guild,
  gold or quest is needed. Old heroes above level 121 can take both steps at once. The Ranger is now called Hunter.
- Each advancement gives three skills and three talents at level 1 (free levels, never refunded) and a **signature
  trait**: Royal Aegis, Conqueror's Dread, Dawnbringer, Hunter's Opening, Rooted Stance, Star Chart, Runescript,
  Elemental Attunement, Collapse, From the Shadows, Soul Harvest, Blood Price.
- **Class armour with its own look** for all twelve classes (Grand Paladin: white and gold plate with a gold cape), plus
  a class weapon and accessory each, sold by the Grand Master's armory and found as loot from level 60 / 120.
- **Who can wear what**: every equipment piece now states its class rule ("For any class", "For Knight class", "For
  Royal Guard and its master classes", "For Grand Paladin only") and the rule is enforced.
- Other players see your current class under your name in its colour. Network protocol 20: update the official server
  with the game.
- Details: [CLASS_TRANSCENDENCE.md](CLASS_TRANSCENDENCE.md).

## BH-035 - Big fights, multiplayer bandwidth, Shadowblade damage, QA - 3 October 2026

- **No more freeze when monsters spawn**: every humanoid monster (and NPC or companion) that appeared rewrote the loop
  settings of animations shared by everyone with that body, and every character rebuilt its animation caches on the next
  frame: 75-140 ms each time. Spawning now costs about 5 ms plus a normal frame.
- **Big fights run about twice as fast**: in a 40-monster brawl the monsters waiting for their turn to attack think and
  collide every other physics step, and distant ordinary monsters and townsfolk animate every second or third frame. On
  the development PC at Low settings the brawl went from 32 ms to 15.6 ms per frame (31 to 64 FPS) and its worst 1% of
  frames from 183 ms to 35 ms. Bosses, heroes, companions and other players are never thinned.
- **Multiplayer uses a quarter of the bandwidth**: hero snapshots go through the room host, which sends them at full rate
  only to nearby heroes on the same map; snapshots are packed into about 45 bytes; unchanged monsters are not re-sent;
  full world checkpoints go out less often. With six heroes on one map the map owner's upload fell from 3.4 Mbit/s to
  0.5 Mbit/s, each member's download from 0.87 to 0.25 Mbit/s and the server's from 2.9 to about 1.1-1.4 Mbit/s. Network
  protocol 19: update the official server with the game.
- **Shadowblade weapons scale with Agility**: daggers, claws and knuckles drew their damage from Strength, so a
  Shadowblade's weapon damage was about a third of the other classes' at level 30. Daggers now use Agility (70%) and
  Dexterity (30%), claws Agility, knuckles Strength and Agility.
- **Balance**: Knight Cleave +12% weapon damage per rank (was +18%); Mage Elemental Attunement 25% (was 10%).
- **Fixes**: the Character window fits its frame with a long rank checklist; the fungal Warren no longer uses the
  drowned Deeps' wet storage; touch-text resizing no longer logs an error for controls freed right after creation.
- Details and measurements: [HANDOFF_bh-035.md](HANDOFF_bh-035.md).

## BH-034 - Ascendant tiers, free VPS hosting, fixes - 3 October 2026

- **Four new rarities above Aether**: Cosmic, Divine, Eternal and Primordial, dropped only by dungeon bosses of level
  70/80/90/100+ (5 %, 2.5 %, 1.2 %, 0.5 % per kill). Forty nine-piece collections, ten of every equipment type per tier,
  each with its own Blender model, icon, animated surface light, motes, ground sigil and light column, a tier signature
  power (Starfall, Judgement, Echo, Eruption) and 2/4/6-piece set bonuses. Class S, SS and SSS guild ranks gate them.
  See [ASCENDANT_TIERS.md](ASCENDANT_TIERS.md). Network protocol 18.
- **Free VPS hosting**: `tools/export_server.py` builds stripped dedicated-server packages (Linux arm64 and x86_64);
  `server/deploy/free-vps.sh` installs them on Oracle Always Free or Google e2-micro in one command. See
  [FREE_VPS_HOSTING.md](FREE_VPS_HOSTING.md).
- **Removed** the stacked-cone pine trees (Ruined Forest, Sanctuary, Westreach).
- **Agdao**: the Crown of Steps stood on the last steps of the terrace stairs, and the hero stuck where the two flights
  met; the pyramid moved 3 m north, leaving a landing. The terrain under the terraces' retaining blocks sat at the
  paving's height and flickered through it all along every terrace edge; it now stays below.
- **Animations after cutscenes**: cutscene actors rewrote the loop settings of animations shared with the player, so the
  hero's run (and walk, strafe, sprint) stopped looping after any cutscene. Actors now use their own copies.

## Chatbox close fix - 2 October 2026

- Chat has a visible X button in desktop and touch layouts. X, Escape and an empty send hide the whole box immediately and release keyboard focus.
- Multiplayer no longer forces a dismissed chatbox to stay visible. New messages briefly show the log, which fades after inactivity; reopening chat keeps its history.
- Chat and network regression suites pass 1,150 checks. Rendered mouse-click checks pass in both layouts. Windows EXE and debug-signed Android APK exports are rebuilt; Android device testing was unavailable.

## Official server and offline/custom game choices - 2 October 2026

- The first menu now offers Official Server, Offline Play and Custom Games. Multiplayer supports 12 players.
- Official accounts use HTTPS, password hashes, recovery codes and server-owned character slots. Existing offline characters can be imported once without changing their local originals.
- Official progress is stored in SQLite with verified backups, exclusive play sessions, revision checks and confirmed save acknowledgements. Official trades commit both players together.
- New custom rooms start with separate local characters, appear through LAN discovery and the shared directory, and can be reopened with Host Again. Existing offline play remains available without internet or an account.
- See `docs/OFFICIAL_SERVER.md` for hosting, backups and the current trusted-friends gameplay scope.

## BH-029 - Zarael Island, the corrupted

Prepared 2 October 2026. Story and geography: docs/LORE.md §11, docs/MAPS.md (Zarael Island); contract and evidence:
work/lemondev/bh-029/.

- **A ship after Kethrax.** Once Kethrax falls, Agdao's ship, the **Sunwake**, lies at a new Marsh Jetty at Wyman
  Outpost. Captain Ilsa Rhondar sails the hero to **Zarael**, the eastern island, and back. Old saves where Kethrax is
  already dead get the ship at once.
- **Agdao.** A new terraced port town bigger than Malasugue: a pier, the Wire Market, five terraces joined by grand
  stairs, lifts and roof footbridges, a council hall and the **Crown of Steps** pyramid. **Terax**, Warden of Agdao,
  greets the hero at the pier in a cutscene and tells of **Aljay**, who cleared the three Vaults two winters ago so
  people could cross the **Bridge of Death**.
- **Act IV - Zarael, the Corrupted.** The Wirekeeper, three chained relay pylons in the Coilwood, the three Vaults,
  the Bridge of Death (Varrogh, the Deathspan Colossus), the Heart Citadel (Orvul Dram, the Leash-Abbot) and the
  Dawn Engine.
- **Four new regions** (levels 30-52): the Coilwood, the Glasswire Barrens, the Bridge of Death and the Heart Citadel,
  plus three Vaults (the Jade Sepulchre, the Obsidian Engine, the Veinworks; levels 33-53) with generated floors.
- **Thirty new monsters** with their own models, from Glyphbound Warriors and Coil Shamans to five bosses.
- **New art.** Town and wilds kits (pyramids, terraces, houses, pylons, the bridge, the citadel), eight texture sets,
  portraits and a painted Zarael atlas. The M map shows whichever island the hero is on.
- **White glows.** Every glow on Zarael is pure white: the Heartwire, glyphs, lamps, pylons, Kharvenn runes and the
  monsters' eyes and cores. Healthy current burns steady and bright; the corrupted current is dim and stutters.
- **Six Agdao townsfolk models**: Terax, Wirekeeper Halvessa Orn, Captain Ilsa Rhondar, and Agdao's porters, traders
  and elders.
- **Cooldowns.** Cooldown Reduction from all sources now stacks to 50% (was 40%), and no skill fires faster than once a
  second.
- **Skill and talent trees fit their window.** Wide trees (the Mage's eight elements) shrink to fit instead of hiding
  columns behind a scroll bar.
- **Fixes.** Projectiles, hazards and skill areas no longer freeze onto the minimap. Lakes and marshes no longer show a
  grid of white discs, and night mist no longer shows round blotches. Leaving efficiency mode after travelling no
  longer freezes the game: it walked a list of lights from maps that had been freed.

## BH-028 - Combat scaling, the Sand Arena, evasion, celestial orbs and the Ascendant dungeons

Prepared 1 October 2026. Design and numbers: docs/COMBAT_SCALING.md and docs/PLAN_bh-028.md.

- **Five Ascendant dungeons behind Kethrax.** Defeating Kethrax opens a rift beside the waypoint on Malasugue's
  Sanctuary Terrace. It leads to **The Sundered Reach**, a broken fortress plaza hanging in the dark, with five gates:
  - The Prismheart Hollows (crystal, 10 floors, levels 80-89), The Underworld of Mourning (a river of the dead,
    12 floors, 86-97), The Aether Reach (floating islands, 13 floors, 92-104), The Eclipse Vault (a black moon,
    14 floors, 100-112) and The Drowned Solarium (a sunken sun-temple, 15 floors, 106-120).
  - Only a **Class A** hero may pass a gate. Their monsters have 50% more health and 30% more damage on every
    difficulty, and the dungeons do not grow extra floors.
  - Each has its own textures, lighting and a centrepiece over its basin, a champion, a Usurper and a new lord:
    Seraphel, Morrowgaunt, Zephyrion, Nocthea and Solmara. Every lord drops its dungeon's celestial orb.
  - Old saves where Kethrax is already dead find the rift open.
- **Evasion works at every level.** Area attacks (blasts, pools, beams, mines, strikes) can now be **grazed**:
  Evasion against four times the attacker's Accuracy, up to 45%. Evasion past the 65% direct-hit cap keeps paying
  off, and the character sheet shows Graze Chance. Second Nature, Slip, Hunter's Calm, Windrunner and Phantom Veil
  now actually work.
- **+50 Maximum HP per level-up** for every hero, old saves included. It stacks with Vitality.
- **Hex of Frailty.** Monsters of level 40+ can curse you: 20% lower resistances and 40% less Evasion for 5 seconds.
  The violet sigil can be dodged, and the curse can be cleansed.
- **Celestial orbs: Sora, Luna, Sol and Airah.** Four new socket crystal families with their own passives
  (Moonveil, Sunflare, Tailwind). Bosses of level 40+ can drop them, and Socket Specialists sell them.

- **No more one-shots at level 40-45+.** Hero, monster and boss numbers are now tied together by one budget
  (`CombatBudget`):
  - **Monster damage follows the average hero's health.** After level 5 it grows exactly as fast as a reference
    hero's health, so a blow takes the same share of your health at level 10, 50 or 300. The level-30/45/60 milestone
    damage bonus is gone, and monster health is one smooth curve with no steps.
  - **Monsters stay within 2 levels of you** from level 30. They used to jump in 15-level steps, so on your 45th level
    every monster grew 15 levels at once.
  - **Vitality.** Every hero gains 16 HP per level after level 5, whatever their build. It shows on the character
    sheet. A level-50 mage with every point in Intelligence has about 1,470 HP, up from 749.
  - **Bosses.**
    - Their attacks hit 20% less overall.
    - Attack multipliers above 1.6 count at half rate, so a 4.2× slam hits like a 2.9× one.
    - Their heaviest critical takes at most about 20% of an average-geared hero's health (five hits).
    - Boss health is unchanged, so fights stay long.
  - **Lethal-blow guard.** No single hit takes more than 35% of a hero's maximum health, or 25% from a boss and 20%
    from another hero.
  - Measured at every level from 10 to 300 for all four classes (`test_bh028`).
- **The Sand Arena at Wyman Outpost.** A lane south of the Fen Road leads to a 40 m ring of sand inside a palisade.
  It has a stone gatehouse, spectator galleries, braziers and broken pillars for cover.
  - Everyone on the sand fights everyone: players, and six randomised adventurers of the party's highest level.
    The adventurers drink, heal, fall back when hurt and use their escape skills.
  - Damage between heroes is scaled so a duel lasts about 10 seconds at any level.
  - A fall costs nothing: you stand up at the gate three seconds later, with full health and a moment's protection.
  - While you are inside, your Tempos, Quake Team and guild fighters wait outside the gate. They follow again when
    you come out.
  - In multiplayer, the host runs the adventurers and blows between machines are resolved on both sides. Network
    protocol is now 14.
- **Fixed:** champion-slaying gear raised a script error when it hit a fighter that is not a monster.

## BH-027 - Alpha Version 0.3: Guilds of your own, accessories again

Prepared 1 October 2026.

- **Accessories drop again.** Monster and chest drops had been restricted to the hero's class gear, and rings, amulets
  and charms count as no class's gear, so they could never drop. They now have their own roll: champions and bosses
  always add one (their second piece), elites often, ordinary monsters about one drop in five, and every chest's
  second piece is one.
- **Twenty new accessories**, each a different shape with its own model, icon, worn model and implicit stats:
  - seven rings: crown, serpent, twin band, star cluster, thorned, skull, moonstone
  - seven amulets: sun, crescent, eye, shield locket, feather, wolf-claw torc, phial
  - six charms: endless knot, dice, spirit bell, stone idol, leaf, hourglass
  - See `game/src/data/data_accessories.gd`.
- **Guilds of your own** (press Z): found a guild, write its motto and Guild Info, and design its banner or upload a
  picture.
  - Adventurers of every class join at levels just below yours, until the guild is full.
  - You can dismiss any member, and expand the guild from 6 slots to 9, 12 and 15 (10,000 / 15,000 / 25,000 gold).
  - Thirteen passives: eight guild passives and five Guild War passives. The Guild War passives grow with the guild
    members fighting beside you.
  - **Call to Arms** summons your members to fight beside you for 15 minutes, with a 30-minute cooldown. It starts
    at one member and can be upgraded to six.
  - See docs/GUILDS.md.
- **Four more guilds** set up in the Guild House, with names rolled from real words (`GuildNames`) and painted banners.
  Their names and terms are rolled once per hero and saved with them.
- **One central Guild Quest Board**, open to every hero whatever their guild: nine postings at a time, fourteen new
  open postings, and five jobs at once. A job from your own guild pays +10%, and handing jobs in earns your guild
  renown.
- **The Guild House was rebuilt.**
  - Six guild counters with banner stands.
  - Your guild is *featured* under the town's plaque: Malasugue believes you can rescue Aljay and Roydo together
    with Paul David.
  - Fellow heroes' banners hang on the north wall.
  - A huge animated banner with your guild's name and motto flies outside once you join or found a guild.
- **Multiplayer** (protocol 13):
  - Every player's guild travels in their profile, and other players' guilds and banners are imported into your
    Guild House.
  - Click a player (or Menu on their party frame) to Whisper (`/w <name>`), Trade, Invite to Guild, Showcase or
    Ping them.
  - Invited players join as Sworn Heroes, receive the guild's passives and banner, and stay in sync with the
    Guildmaster.
  - Call to Arms fighters fight in multiplayer too.
- **Showcase**: after the other player agrees, both of you see both heroes' equipped gear and weapons side by side
  (no stats) and each hero's guild. Click a guild to see its enlarged banner and info.
- **Pickup fixes.**
  - A drop from a monster that died in the air or over a ledge fell no further than 4 m and could hang out of
    reach. It now falls to the first walkable ground (and settles again if it lands on nothing).
  - A ground tag hovered while the loot tags were shown stayed the click target after they were hidden.
  - A drop that auto-loot wanted but could not take flew back and forth every quarter second.
- **Old saves and the survival rebalance.** The level-reward points credited to an old save by the rebalance
  (free points 3 → 10 and skill points 1 → 2 per level) used to sit unspent, so an old hero's HP and Mana stayed
  below a new hero's. The credited attribute points are now spent on load along the hero's own build, and a notice
  shows the new Maximum HP and Mana. Skill points stay yours to place.

Sources: docs/GUILDS.md, game/tests/unit/test_bh027.gd, game/tests/unit/test_bh027_pickup.gd,
game/tests/unit/test_survival_balance.gd, work/lemondev/bh-027/evidence.

## BH-026 - The Ember Dragon set

Prepared 1 October 2026.

- The sculpts in models/special_weapons/ are in the game as the **Ember Dragon** set, the last Legendary set Aljay wore while he was still human: the **Ember Dragonslayer** (sword), the **Aegis of Fragnir** (shield) and the **Ember Dragonhide** (cuirass). Knights only (Swordsman and Warden Tempos too). Two- and three-piece set bonuses; the full set ignites enemies.
- The cuirass is fitted to the hero's body: it sits as sculpted in the idle pose, its pauldrons follow the arms, and it follows the body sliders. The sword and shield keep the sculpts' painted colours. Knight-type Tempos wear the cuirass too.
- `alj` now gives the whole set as Unbound copies with four open sockets: no level or attribute requirement, wearable from Class E. Unbound gear asks for Class E (it asked for no class before).
- The pieces are story pieces: never loot, stock or crafts.

Sources: docs/SPECIAL_WEAPONS.md, game/tests/unit/test_bh026.gd, work/lemondev/bh-026/evidence.

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
