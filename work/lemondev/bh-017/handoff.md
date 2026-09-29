# bh-017 handoff — trade rows, 10 new buffs/debuffs, class-biased drops, Quake Team, Enchantment + Fore-Tech, guild name and banner

Status: **IMPLEMENTED — UNVERIFIED for independent review.** Verified in the real runtime on this PC (Godot 4.7.2, 1916x1011);
no blind critic, no phone test (APK rebuilt only). Evidence: `evidence/shots/*.png`, `evidence/tests_final.txt`, new suite `test_bh017`.

## 1. Merchant Row in every town (DataTownRows, TownRowBuilder, TownSign)
Malasugue **Merchant Row** (south-east of the plaza), Olivar **Market Row** (south-west), Wyman **Quartermaster Row** (south of the
bonfire). Each is one paved street with a stand for every merchant, the rare dealer (Malasugue), the three crafting stations
(Alchemy Table, Workbench, Forge) and the Tempo shrine (Malasugue: Veyra moved here). NPC positions come from the same table
(`DataTownRows.npc_spot`), so map and NPCs cannot drift apart. Stands are marked the medieval way — **the trade's own object hangs
from an iron arm** (flask, ring, shield, scroll, anvil) and turns in the breeze; the stand's name shows as a normal name plate
when you come near. No lettered boards, no arches (both were tried and removed on feedback). Old market stalls, smithy yard and
the Shrine of the Fallen were removed from their old spots; the burnt house moved west; dialogue and guide text point to the row;
world-map places/roads updated (`town_market`=Merchant Row, `olv_row`, `wy_forge`=Quartermaster Row).

## 2. Five buffs + five debuffs (StatusRules)
Debuffs: **Grievous Wound** (healing AND regeneration received -25% per stack, 3 stacks = -75%; applied in `Actor.heal` and the
Player/Tempo regen ticks via `StatusController.heal_taken_mult`), **Enfeebled** (-20% all six attributes), **Dazzled** (-50%
Evasion, -30% Accuracy), **Sundered** (-25% Defense, +10% damage taken), **Demoralized** (-15% damage dealt, -15% crit damage).
Buffs: **Vigor** (+15% max HP, +25% healing received), **Keen Focus**, **Windstep**, **Titan's Might** (+15% attributes),
**Spirit Ward**. Sources: monsters (Shade Stalker, Ghoul Brute, Ashen Cultist, Grave Archer, Aether Wisp, Ogre, Necromancer,
Plague Bloater ...), knight/shadowblade skills (Shield Bash, Judgment, Eviscerate, Crippling Star), five elixirs and two throwable
flasks (Blinding Flask, Festering Bomb) — craftable, sold by Tovin/Pell/Hobb. `dazed`/`blinded` (used by monsters but undefined,
so they did nothing) are now real statuses. 10 new SVG status icons, 7 new item models/icons (hue-shifted from existing ones).

## 3. Equipment drops follow the hero's class (ItemGenerator.class_fit / random_base)
72% of class-hinted picks come from the class's own gear (weapons it has mastery in, its armor weight, shields for knights);
measured 78-86% class gear overall for all four classes. Applies to monster drops, chests, caches, mimics, set/unique rolls and
class-hinted merchant stock.

## 4. `quake team` cheat (core/quake/*, actors/tempo/quake_ally.gd)
Type `quake team` in chat: an AI ally **hero** joins (max 3, Single Player only — refused in multiplayer). Each is a whole
HeroData (class, level = yours, attributes auto-spent, gear, bag, gold) on top of the Tempo fighting AI: follows, stands between
monsters and you, class skills, retreats, evades, drinks draughts, is healed by your Tempos/skills. In town it **walks the
row stand to stand**: buys the gear that makes it strongest (`QuakeBrain.rating` simulates wearing each candidate), wears it, sells
what it replaced, keeps health/mana draughts, and binds one Tempo at the shrine. It earns a share of every kill's gold. Knocked out
= back on its feet after 14 s. Saved in the hero (`quake_team`, optional key). Classes: Mage, Knight, Ranger, Shadowblade (never
the leader's own).

## 5. Enchantment and Fore-Tech (DataUpgrades, WeaponUpgrades, WeaponUpgradePage)
Two separate weapon upgrades, both stack on one weapon. **Enchantment** (Alchemy Table): a rune, rank I-III, converts 20/30/40% of
the damage to an element and adds elemental gifts (Flame, Frost, Storm, Stone, Radiant, Umbral). **Fore-Tech** (Forge): a
mechanical refit +1..+5, +2% weapon damage per rank plus a bonus (Whetted Edge, Balanced Grip, Serrated Teeth, Weighted Head,
Piercing Point, Fine Sights); shows as "+N" in the name. A different rune/refit starts over at rank 1. Tabs in the crafting window.

## 6. Guild name and banner (GuildRules, GuildCustomWindow, GuildBannerDisplay)
After joining a guild (and any time from the Guild House board or by clicking the guild in the Character window) you may rename it
(32 chars, brackets/control chars stripped) and upload any PNG/JPG/WebP (native file dialog, or drag a file onto the window). The
picture is cropped to 2:3, stored as a small JPEG inside the save (optional keys `guild_alias`, `guild_banner`), shown in the
window, the Character window and on the wall of the Guild House. Not tested on a phone (file picker).

## Not done / next
Independent review; phone test; multiplayer does not show other players' guild banners.
