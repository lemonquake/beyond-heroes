# Bloodbinder (`bloodbinder`)

- Module: `tools/blender/characters/enemy_bloodbinder.py` (started by Builder A, finished by Builder A2; kits: `enemy_bandit_cutthroat` SB, `enemy_ashen_cultist` robe/sleeve, `enemy_hollow_soldier` cloth weights, `kit_a_common`, `kit_e_orrery`)
- GLB: `game/assets/characters/bloodbinder.glb` (3.1 MB) + `bloodbinder.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 11920 (budget 20k); 24 bones; 9 materials; 6290 verts
- Height: 1.9 m (SCALE = 1.9 / 1.83; T-pose top 1.902 m, idle f0 1.889 m). The high collar rises to ~1.81 m behind the head.
- Clips (48): the 42 shared enemy base clips + `dagger_1 dagger_2 dagger_heavy cast_quick cast_heavy cast_area`
- Weapon: hooked sickle rigid on `weapon.R` (weapon verts deform with the hand, `K.enable_weapon_deform`). Left hand is empty (open, bare, veined) - the casting hand. Stance clip: `idle_dagger`.

## Palette (`bloodbinder`, exported as `BH_*__bloodbinder`)
| material | use |
|---|---|
| BH_Cloth_Primary (0.24, 0.018, 0.03) | dark crimson robe, collar lining, left sleeve roll, right cuff |
| BH_Cloth_Secondary (0.018, 0.014, 0.016) | black under-robe / front slit panel, high collar outside, cincher, right sleeve |
| BH_Skin (0.72, 0.67, 0.66) | corpse-pale hollow-cheeked face, bare left forearm + hand |
| BH_Hair (0.025, 0.018, 0.02) | long dark hair: domed cap with parting, back hair, two front curtains to the chest |
| BH_Leather | cincher straps, hip vial belt, bandolier, vial loops, boots, sickle grip |
| BH_Steel (silver) | buckles, vial caps, collar rim, throat chain, sickle inner edge |
| BH_DarkSteel | sickle crescent + fittings |
| BH_Shadow | eye sockets, mouth, nails |
| BH_Emissive (1.0, 0.08, 0.06) x10 | blood-light: 8 hip vials + 6 bandolier vials, eyes, left forearm/hand veins, sickle blood groove + pommel jewel, throat and bandolier jewels |

## What makes it distinct
Silhouette: a tall, narrow robed figure with a huge stiff flared collar standing round the back of the head (black outside, crimson inside, silver rim) - at the gameplay camera it reads as a red-lined halo-ring around a dark head, unlike any hood/cowl caster. Hooked sickle in the right hand, one bare pale forearm on the left. Palette: the only crimson-and-black caster; emissive is a saturated blood red (the ashen casters glow orange, goblin summoner green, orc shaman pale cyan). The glow is spread in small points (vial rows on the hip belt and diagonal bandolier, veins, eyes) rather than one big light.

## Evidence
- `bloodbinder_rest_iso.png`: T-pose front/back, idle_dagger at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `bloodbinder_clips.png`: idle_dagger, every attack clip, hit_heavy, death_back.
- `logs/bloodbinder_metrics.json`: worst absolute edge growth 0.058 m (strafe_r, robe side at the waist); arm clips ~0.054 m at the shoulder sleeve.
- `logs/godot_check_bloodbinder.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 clips present with the meta lengths, `block_loop` keeps its name; loops applied at runtime from the meta.

## Build log
```
[bloodbinder] mesh 11920 tris, 152 parts, 0.9s
[bloodbinder] baked 48 actions in 18.8s
23:30:46 | INFO: Finished glTF 2.0 export in 3.5069124698638916 s
[bloodbinder] clip lengths verified (48 clips)
[bloodbinder] -> A:\Python\beyond-heroes\game\assets\characters\bloodbinder.glb (3.1 MB)
[build] done in 23.6s
```

## Revision passes
1. The kit hair cap (built on the unnarrowed kit head) closed with a flat fan and read as a flat-topped "top hat"; replaced by a module hair cap on the narrowed head rows that closes into a domed crown with a centre parting. The brow ridge (a thick pale bar) was thinned and pushed into the head. Vials enlarged (hip 9 cm, bandolier 8 cm) so the red points read at the gameplay camera.

## Known limitations
- The collar is a single-thickness sheet (two faces, black out / crimson in, no thickness between them); it is rigid on `chest`, so in extreme head turns the head can approach the collar edge.
- Veins on the bare forearm are thin emissive tubes; at 22 m they merge into a faint red tint on the pale arm rather than readable lines.
- Front hair curtains are rigid-ish tubes weighted chest/neck/head; they do not swing.
