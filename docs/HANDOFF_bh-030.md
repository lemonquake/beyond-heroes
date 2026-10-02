# bh-030 handoff: Debug console, gear that scales, dynamic Guild Quests, belt keys, profile pictures, first person, server UI, AoE crash fix

## Crash fix: many monsters dying at once under area spells

`SafeCallable` (`src/combat/safe_callable.gd`). Projectiles, delayed blasts, sweeps, orbs, sentries, traps, hammers and
storm areas stored lambdas written inside the node that made them, such as an Enemy or a skill node. When that node was
freed before the effect fired (a monster killed while its blast was still in the air), even `is_valid()` on the lambda
read freed memory. Godot printed `Condition "slot >= slot_max"` and `Trying to call a lambda with an invalid instance`,
and this could take the whole game down. Every stored callback now records its owner's id when it is assigned, and the
effect checks that id before touching the callable. Two "previously freed" source checks were also reordered
(`area_effects.gd`, `projectile.gd`), and `SkillRunner._hit` ignores a freed caster or target.
`tests/tools/stress_aoe.tscn` reproduces the case: a level 53 hero with every spell, no cooldowns and one-hit kills,
in waves of 100+ monsters. Before the fix it logged the errors; after it, all four classes run clean.

## Gear scaling (`src/core/stats/gear_scaling.gd`)

- Defense: every slot follows a reference curve built from the authored bases, carried past the last tier so a full
  plate kit keeps ~58-60% physical reduction against same-level monsters from level 50 to 300. Every slot is worth at
  least a share of a chest of its level (`SHARE`). Cloth = 55% of plate. A base keeps its character (0.85x-1.3x).
  Plain Common plate: L20 chest 83 / gloves 42, L30 130 / 65, **L53 265 / 132**, L100 496 / 248.
  Levels 1-5 are unchanged. Tuning knobs: `SHARE`, `CLOTH`, `LATE_BONUS`, `LATE_SPAN`.
- Flat enchantments and flat implicits that are sizes (Health, Mana, attributes, regeneration, Defense, added damage,
  Evasion) grow past their affix's top-tier level. Percentages, chances and skill levels never scale.
  This is applied at read time (`ItemInstance.affix_value / implicit_value`), so existing items benefit too.

## Debug console (`src/ui/windows/debug_window.gd`)

`azrin azrael` unlocks it per hero (`HeroData.debug_unlocked`, an optional save field). A Debug button appears beside the
hero's name, and F2 also opens it (`debug_console`). It has seven pages; see docs/CHEATS.md. The switches live on `Game`
(`debug_damage_mult`, `debug_one_hit`, `debug_no_cooldowns`, `debug_speed_mult`, `debug_freeze_ai`, `debug_xp_mult`,
`debug_gold_mult`, `debug_min_drop`) and are never saved. `quake quake` dismisses the newest Quake Team ally
(`QuakeTeam.dismiss`).

## Dynamic Guild Quests

`DataGuildJobs.DYNAMIC` builds postings from the world itself: Delve, Dungeon bounty, Lord hunt, Expedition and Purge
for every dungeon the hero can reach, plus Patrols for discovered combat maps. Ids are `dyn:<kind>:<target>` and are
saved like any other job. About 45% of the board is dungeon work. The old templates no longer stop at level 60. The new
**Post New Jobs** button reposts the whole board.

## Belt keys

`HeroData.BELT_SIZE` is 6: Q, E, plus four quick keys (`quick_1..4`, Alt+Q/W/E/R by default). The quick slots are empty
by default. Key descriptors now keep modifiers (`{"type": "key", "code", "alt"}`), and `HotkeyCapture` rebinds a key
from anywhere. The Inventory's Potion & Scroll Belt is pinned along the bottom with all six key slots. The HUD bar and
the touch controls (between the orbs) show the quick slots too. Alt+Q does not also fire Q, and Alt+R does not also
interact.

## Profile pictures

`ProfilePicture` stores a 192x192 JPEG in `HeroData.profile_pic` (an optional save field). It is set from the Character
window (Picture... / Remove, or drop a file). `Net.send_profile_picture_all()` sends it once per player and per change.
It shows on the HUD portrait, party frames and the player menu. Guild banners already travelled this way (bh-027).
The network protocol is now 16 (game and `server/service.py`): a new RPC shifts Godot's RPC layout, so mixed versions must refuse each other. Restart the official server after updating.

## First person

Toggle with V or Settings > Gameplay (`Settings.first_person`, `fp_fov`). `PlayerCamera.first_person` places the eye at
1.62 m, slightly in front of the face. Mouse look is captured while no window is open; on touch, drag the view.
`Player._update_fp_aim` aims at the crosshair and projectiles keep its elevation. Probes (save slot 90+) never write
the setting.

## Server menu (`src/ui/menu/server_menu.gd`, `saved_accounts.gd`)

The rewrite keeps the same signals and public methods. The home page has three realm cards and custom games as cards.
The Custom view has hosting plus a full list. Sign-in is a large two-column page with saved accounts (an encrypted
per-device file; the password is kept only when "Remember my password" is ticked) and confirms with "Account created
successfully". The Characters and Import pages are also cards. Layouts reflow by width and use bigger targets on touch.

## Evidence

`work/lemondev/bh-030/evidence/*.png` (`tests/tools/capture_bh030.tscn --phase=belt|debug|fps|guild|profile|server`).
Tests: `tests/unit/test_bh030.gd`.

## Not done / notes

- `docs/CHEATS.md` had an uncommitted stray line before this run (a token-like string on line 2). It was left as found.
- The first-person view shows the hero's own body when looking down. Helmets with inside faces were not checked one by
  one.
