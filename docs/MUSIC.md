# Music and sound (bh-025)

The recorded pack in `audio/` is in the game: seven themes and twenty-five weapon and spell sounds. One autoload,
`Music` (`game/src/autoload/music_director.gd`), decides what plays.

## What plays where

| Track | File | Plays |
|---|---|---|
| `main_theme` | `main_theme.mp3` | **The default.** The main menu, the towns (Malasugue Town, Olivar, Wyman Outpost) and their houses, the roads of Westreach, and any map whose music is unset or unknown. |
| `battle_theme` | `battle_theme.mp3` | While monsters are fighting the hero in open country, and while a dungeon's champion is. |
| `boss_theme` | `boss_theme.mp3` | From the moment a boss sees the hero until it falls or loses them; the Hollow Throne and the Weeping Causeway until their boss is down; Kethrax's introduction. |
| `dungeon_theme` | `dungeon_theme1.mp3` | The Ruined Forest, the Catacombs, the Forgotten Temple and every dungeon without a theme of its own. |
| `fire_dungeon_theme` | `fire_dungeon_theme.mp3` | Emberforge Depths. |
| `ice_dungeon_theme` | `ice_dungeon_theme.mp3` | Rimeglass Barrow and Prismdeep Geode. |
| `aljay_theme` | `aljay_theme.mp3` | Paul David speaking of Aljay and Roydo (below), his tale (`the_three`) and the chain breaking (`chain_breaks`). |
| `music_legend` | `music_legend.wav` | The prologue (synthesised; kept from before). |

A map names its track in `MapDef.music`. The four synthesised tracks the recorded themes replaced (menu, town,
dungeon, boss; 80 MB of WAV) are no longer in the build; `tools/audio/build_all.py --only music --names music_town`
still renders one.

## Layers

The director adds up four layers, highest first:

1. **Override**: a cutscene (`Cutscene.music`) or a conversation (a dialogue node's `"music"`) asked for a track.
2. **Boss**: a boss is engaged within 45 m.
3. **Battle**: a monster is engaged within 45 m on a map that is not a dungeon, or a champion is anywhere. It lets go
   after 6 s without a fight. Settings > Audio > **Battle Music** turns this layer off (bosses still bring theirs).
4. **Base**: the map's track.

Tracks crossfade on an equal-power curve (0.8 s into a fight, 3 s out of it, 2 s between maps). The exploring themes
remember where they stopped for three minutes, so the road's music carries on after a fight instead of starting over.
The pause menu puts the music behind a low-pass filter. Three stingers play over it while it steps back: a boss has
seen the hero, a boss is down, the hero has fallen.

## Volume

Music sits on its own bus at **60 %** (`Settings.music_volume = 0.6`) until the player moves Settings > Audio > Music;
the choice is saved in `user://settings.cfg`. "Restore Defaults" on the Audio tab returns it to 60 %. Each track also
carries a fixed trim (`TRACKS[...].gain`) that levels the seven recordings to about -18 LUFS, so the main theme
(recorded 5 dB quieter than the rest) is not lost beside the battle theme.

## Paul David

Nine of his dialogue nodes carry `"music": &"aljay_theme"`: the shard, what follows the tale, his brand and orders,
"What was Aljay like?", "And Roydo?", his report after Kethrax, the three chains and the Black Spire. The theme
starts on the first of them and holds until the conversation ends; small talk before the shard keeps Olivar's music.
The cutscene he tells plays the same track, so talk, tale and talk again are one unbroken piece.

## Sounds

Recorded (from `audio/weapon/`, cut to the sound itself and levelled by `tools/audio/import_pack.py`):

| Sound | Used by |
|---|---|
| `attack_woosh` | Sword, spear and javelin swings |
| `sword_hit` 1-3 | Sword hits |
| `axe_hit` 1-3 | Axe hits |
| `hammer_hit` 1-3 | Club (maces, hammers, cudgels) hits |
| `hit_metal` (`generic_hit_metal`) | Blows landing on the armoured dead and on Morthar |
| `bow_attack` 1-3 | Bow shots |
| `cleave` 1-2 | Cleave |
| `mage_attack` 1-2, `mage_strong_attack` | Staff and wand attacks; their heavy attack |
| `fireball_cast`, `fireball_hit` | Firebolt |
| `meteor_cast`, `meteor_hit` | Meteor Strike |
| `blizzard_cast` | Blizzard |
| `chain_lightning` | Chain Lightning |

Made for this update:

- From the recordings: `greatsword_hit` and `greataxe_hit` (the same steel slowed, over a low thump), and two more
  pitches each of `attack_woosh` and `hit_metal`.
- Synthesised (`tools/audio/sfx_bank.py`): `dagger_hit`, `spear_hit`, `claw_hit`, `fist_hit` (knuckles), `magic_hit`
  (staff and wand bolts), `crossbow_fire`; `heartbeat` (low health), `ui_buy`, `ui_craft`, `loot_pickup` (gathering)
  and `holy_cast`, which the game already asked for and did not have; the stingers `sting_boss`, `sting_victory`
  and `sting_defeat`.

## Rebuilding

```
pip install miniaudio
python tools/audio/import_pack.py          # audio/ -> game/assets/audio (sfx cut and levelled, music copied)
python tools/audio/build_all.py --only sfx # the synthesised sounds
godot --headless --path game --import
```

Tests: `game/tests/unit/test_bh025.gd`. Live check: `game/tests/tools/probe_bh025.tscn` (run with
`-- --class=knight --map=sanctuary --slot=97`); it walks town, road, fight, Paul David and a dungeon and prints what
plays.
