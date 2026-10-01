# Handoff: bh-027 (Alpha 0.3)

The state of `main` after Alpha 0.3, and how to carry on from it.

## What shipped

Full notes are in docs/CHANGELOG.md (BH-027). The guild design is in docs/GUILDS.md.

- **Accessories.**
  - The drop bug is fixed: rings, amulets and charms now have their own roll (`Loot.accessory_slot`), plus
    `ItemGenerator.accessory_fits`.
  - There are 20 new accessories (`data_accessories.gd`). Their shape builders are in `tools/blender/items/item_gear.py`;
    the worn models come from `tools/blender/hero/hero_wear_ends.py` (JEWELS).
- **Guilds.** The guild code lives in `src/core/guilds/`:

  | file | what it does |
  |---|---|
  | `guild_registry.gd` | the one shape every guild has |
  | `own_guild.gd` | founding, members, recruitment, slots, passives, treasury, saving |
  | `guild_summons.gd` | Call to Arms |
  | `guild_names.gd` | guild name generator |
  | `guild_banner_art.gd` | painted banners |
  | `guild_jobs.gd` | the central quest board |

  Tuning numbers are in `src/data/data_guild_passives.gd`. The UI is the `guild`, `guild_detail` and `showcase` windows
  plus `PlayerMenu`; the Guild window opens with Z.
- **Guild House.** The interior is `world/maps/interior.gd` `_guildhouse()`. The pieces in it are `world/guild_counter.gd`
  and `world/guild_banner_display.gd` (the featured banner). The big banner outside is `world/guild_hall_banner.gd`,
  placed by `world/maps/sanctuary.gd` at `GUILD_BANNER_AT`.
- **Multiplayer.** Protocol 13. The new code is the bh-027 section at the end of `src/net/net.gd`: guild profile,
  banner exchange, whispers, invites, sync, kick/leave, Showcase. Sync and import only send or emit when something has
  changed; without that guard, profile updates fed back into each other in a loop.
- **Pickup.**
  - `Loot.landing_point` / `floor_under(depth)`: a drop that finds no floor below falls up to 80 m to the first
    walkable ground.
  - `LootDrop._settle()`: re-checks each drop's footing once after it lands.
  - The stale-hover fix is in `LootLabels`.
  - The auto-loot retry backs off for 4 s.
- **Old saves.** `HeroProgress.POINT_RULES_VERSION = 2`. Old saves get their credited rebalance points spent along the
  hero's build (`allocate_along_build`). `Game._rebalance_notice` shows a one-time notice.

## How to verify

```sh
GODOT=<godot 4.7.2> bash tools/run_tests.sh            # full suite takes ~15 min; test_balance alone is ~6 min
godot --headless --path game res://tests/run_tests.tscn -- --only=test_bh027,test_bh027_pickup
# two-process network probe (two terminals, or background the host)
godot --headless --path game res://tests/tools/net_probe_guild.tscn -- --role=host --class=knight --slot=94 --map=sanctuary
godot --headless --path game res://tests/tools/net_probe_guild.tscn -- --role=join --class=mage --slot=93 --map=sanctuary
# screenshots (needs a display; xvfb-run works with --rendering-driver opengl3)
godot --path game --resolution 1916x1011 res://tests/tools/capture_bh027.tscn -- --class=knight --slot=97
```

The baseline on `main` before this work already had **36 failing checks**:

| suite | failing checks |
|---|---|
| test_balance (power band) | 11 |
| test_enemies2 | 8 |
| test_inventory_overhaul (bow/crossbow/javelin Str-Dex) | 15 |
| test_bh017 (Fore-Tech) | 1 |
| test_dungeon_growth (guardian elite abilities) | 1 |

They have nothing to do with this work and are still open. `test_tempos.test_every_skill_works_live` (ar_pierce) can
fail when the machine is busy and passes alone.

Rebuilding assets (Blender 5.2):

- `build_items.py -- all <ids>` builds models and icons.
- `hero_wear.py -- <ids>` builds worn models. It needs `work/lemondev/bh-023/scratch/hero_mesh.npz`, which comes from
  `hero_body.py -- export`. That export also rewrites `hero.glb`; restore it with `git checkout`.
- The pipeline produces byte-identical output for unchanged items.

## Open ends / ideas

- The great banner outside stands about 6 m tall. Seen from the plaza, its top sits at the edge of the top-down
  camera's view; the whole banner shows when you walk up toward the door. Leaning the cloth back toward the camera
  would make it read from farther away.
- Guild War has passives but no mode of its own: there is no PvP or guild-vs-guild event yet. The passives count Call
  to Arms fighters and guildmates on the same map.
- Rolled guilds' counters have no clerk NPCs; you register through the guild's page.
- A Showcase that the other player declines sends no answer, so the asker only sees "request sent".
- Fellow players are matched by hero name, as chat already does. Two players with the same name in one session would
  be ambiguous for guild invites. `peer_by_name` never matches this machine's own hero.
