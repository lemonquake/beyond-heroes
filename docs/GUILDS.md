# Guilds (Alpha 0.3, bh-027)

Press **Z** for the Guild window (rebindable in Settings > Controls; the touch Menu has a Guild tile).

## The guilds of Malasugue

The Guild House now hosts six guilds at once: the **Swordfin Company** and the **Lantern Covenant**, plus four
newer guilds rolled once for each hero and saved with them. Their names come from `GuildNames`, which builds names
only from real words with a few naming patterns, so a name never comes out as syllable soup. Some examples:
*The Iron Stags*, *Order of the Gilded Anchor*, *The Saltmarsh Wardens*, *Emberhold Vanguard*,
*The Wolf and Anchor*, *The Wandering Compass Company*, *Keepers of the Silver Tide*. Place names are two real
words joined together (Ash + vale, Gull + harbor). Each rolled guild has:

- a Guildmaster
- a motto
- a hall
- a painted banner (`GuildBannerArt`: field colour, pattern, gold or silver trim, crest)
- three perks per tier step
- one house rule (bounty gold, potion healing or a cheaper inn)

You register with a rolled guild at its counter, the same way as with the two old guilds.

## The Guild Quest Board (central)

All guilds post on **one** board in the middle of the hall, and **any hero may take any job**, in a guild or not.

- The board shows nine postings at a time, drawn from every guild. Fourteen new "open" postings have been added; one
  of the rolled guilds issues each of them, and sometimes your own guild does.
- You can carry **five** jobs at once (it was three).
- Your tier bonus still applies. A job your own guild posted pays **+10%**.
- Every job you hand in earns your guild renown.

## Founding a guild

Use the Guild window's **Found a Guild** page, or ask Steward Hollis. The charter costs **1,000 gold**. On that page
you:

- type a name or press **Roll a Name**
- write a motto (or roll one)
- write the **Guild Info**: what the guild is about, shown on its page and in Showcases
- design the banner: 12 field colours, 7 patterns, 14 crests, gold or silver trim

After founding you can also upload your own picture as the banner (Overview > Rename & Upload Banner). The founder
becomes the **Guildmaster** and keeps their hero tier. While you lead a guild you cannot join another one; disband
yours first.

## Members

Adventurers of every class apply on their own while a slot is free. The first arrives after about 40 seconds of
play; after that, one arrives roughly every 3½ minutes. **Open Doors**, your tier and your guild's level shorten the
wait. Recruits arrive at levels a little below yours: 35% below up to your own level, so a level 20 Guildmaster
draws levels 13–20. **Veteran Training** narrows that range.

Each adventurer has:

- a **trait**: Stalwart, Keen-Eyed, Swift, Brash, Scholar, Merchant-Born, Loyal, Veteran, Field Medic or Berserker
- **loyalty**, which grows over time and sets their title: Recruit → Veteran → Officer → Champion
- the **renown** they have earned for the guild

While they are in the guild, members:

- earn the guild renown (its level, up to 20)
- pay tithes into the treasury (collect them on the Overview page)
- train: members below your level occasionally gain a level, and when you level up, anyone below the recruit range
  catches up

The Guildmaster can **dismiss** anyone, including fellow players.

**Slots:** 6 at the start. Expanding to 9 costs 10,000 gold, to 12 costs 15,000, and to 15 costs 25,000.

## Passives

Ranks cost gold and need a guild level. Guild passives start at guild level 1 and their later ranks need two more
levels each. Guild War passives start at guild level 4.

| Guild passive | Per rank | Max rank |
|---|---|---|
| Sharpened Steel | +2% Damage | 5 |
| Iron Discipline | +2.5% Maximum HP | 5 |
| War Chest | +4% Gold Find, larger tithes | 5 |
| Scholars' Hall | +3% Experience | 5 |
| Swift Banners | +1.5% Movement Speed | 4 |
| Quartermaster | +6% Potion Effectiveness | 4 |
| Open Doors | adventurers apply 18% sooner | 3 |
| Veteran Training | narrower recruit range, faster training | 3 |

**Guild War passives** are meant for fighting alongside many members at once. Each counts every guild member
fighting within 30 m of you, up to 12:

- your **Call to Arms** fighters
- in multiplayer, every guildmate on your map: members of your guild, or players in the same old guild

| Guild War passive | Per rank, per comrade |
|---|---|
| Rallying Cry | +0.8% Damage |
| Shield Wall | +1.5% Defense |
| War Drums | +0.5% Attack Speed |
| Blood Oath | +0.15% Life Leech |
| Siege Masters | +1.2% Damage to Champions |

## Call to Arms (the Guildmaster's active skill)

Call to Arms summons your strongest members to fight beside you for **15 minutes**. You can use it again **30
minutes** after each call.

- **Rank 1 calls one member.** Each rank calls one more, up to six members at rank 6. Training a rank costs
  3,000–32,000 gold and needs guild level 3, 6, 9, 12 or 15.
- The fighters are whole heroes at their own level and class, in gear of their level. Their trait shapes how they
  fight.
- They follow you through doors and waypoints, and they get back up if they fall.
- In multiplayer, other players see them, labelled with your guild's name.

## Multiplayer

The network protocol is now **13**.

- **Guild data in profiles.** Every player's profile carries their guild. Uploaded banners are sent once per player
  and again whenever they change.
- **Imported guilds.** Other players' guilds are imported into your world and hang on the Guild House's north wall.
  You can browse them under **All Guilds**.
- **The player menu.** Click another player's hero (or **Menu** on their party frame) and choose:
  - **Whisper**: opens the chat with `/w <name> ` filled in. `/w`, `/whisper` and `/tell` all work.
  - **Trade**
  - **Invite to Guild**: the player who accepts joins as a *Sworn Hero*. They get the guild's name, motto, info,
    passives and banner, and the Guildmaster's later changes reach them while you both play. Dismissing or leaving
    is sent to the other player.
  - **Showcase**: see below.
  - **Ping**: marks where that player stands.
- **Showcase.** The other player is asked whether to show their gear. If they say yes, you **both** see both heroes
  side by side: each on a turning plinth, with every equipped piece and weapon (hover for the item card), and no
  stats. Each side shows that hero's guild; click it for the guild's page with its banner enlarged, motto,
  Guildmaster, level, members, **Guild Info** and what it grants.

## The Guild House

The Guild House has been rebuilt as a 28 × 16 m hall:

- **North wall:** the old houses' banners. When you found a guild, your banner hangs **featured** at the head of the
  hall, with the town's plaque underneath: Malasugue believes you can rescue its hometown heroes, **Aljay and Roydo,
  together with Paul David**. Steward Hollis tells you so the next time you talk.
- **Side walls:** the four rolled guilds, each with a counter and a banner stand.
- **North wall, between the banners:** the banners of fellow heroes' guilds.
- **Centre:** the one Guild Quest Board.

**Outside**, a huge animated banner flies beside the door once you join or found a guild. It is 3.6 × 4.8 m of
cloth between two 6 m poles, rippling in the wind, with your guild's banner, its name across the top and its motto across
the foot.

## Code map

| | |
|---|---|
| `src/core/guilds/guild_names.gd` | name and motto generator |
| `src/core/guilds/guild_banner_art.gd` | painted banners |
| `src/core/guilds/guild_registry.gd` | every guild a hero knows, one shape (`info`, `banner`), rolled and imported guilds |
| `src/core/guilds/own_guild.gd` | founding, members, recruitment, slots, renown, passives, treasury, saving, snapshots |
| `src/core/guilds/guild_summons.gd`, `src/actors/tempo/guild_fighter.gd` | Call to Arms |
| `src/data/data_guild_passives.gd` | costs, passives, traits, timings |
| `src/core/guilds/guild_rules.gd`, `guild_jobs.gd` | membership and perks for every kind of guild; the central board |
| `src/net/net.gd` (section bh-027) | profiles, banners, invites, sync, whispers, Showcase |
| `src/ui/windows/guild_window.gd`, `guild_detail_window.gd`, `showcase_window.gd`, `src/ui/widgets/player_menu.gd` | UI |
| `src/world/guild_counter.gd`, `guild_hall_banner.gd`, `world/maps/interior.gd` | the Guild House |
| `tests/unit/test_bh027.gd` | tests |
