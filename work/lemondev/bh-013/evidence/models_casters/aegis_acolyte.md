# Aegis Acolyte (`aegis_acolyte`)

- Module: `tools/blender/characters/enemy_aegis_acolyte.py` (Builder A2; kits: `enemy_bandit_cutthroat` SB/head/belt/boots, `enemy_ashen_cultist` robe/hood/sleeves, `enemy_hollow_soldier` cloth weights, `kit_a_common`, `kit_e_orrery`)
- GLB: `game/assets/characters/aegis_acolyte.glb` (3.2 MB) + `aegis_acolyte.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 14902 (budget 20k); 24 bones; 9 materials; 7810 verts
- Height: 1.85 m nominal (SCALE = 1.85 / 1.9); hood crown 1.88 m; the gold halo behind the head rises to 2.02 m (T-pose top 2.023, idle f0 2.005).
- Clips (47): the 42 shared enemy base clips + `shield_bash sword_1 sword_2 cast_quick cast_area` (`taunt` is in both lists, so 47 unique).
- Weapons: kite shield rigid on `weapon.L` (face toward -Y, same convention as the hero shield), flanged mace rigid on `weapon.R` (weapon verts deform, `K.enable_weapon_deform`). Stance clip: `idle_shield`. `sword_1` / `sword_2` are the mace swings, `shield_bash` the shield strike.

## Palette (`aegis_acolyte`, exported as `BH_*__aegis_acolyte`)
| material | use |
|---|---|
| BH_Cloth_Primary (0.8, 0.78, 0.72) | white robe, hood, sleeves, shield face |
| BH_Cloth_Secondary (0.6, 0.4, 0.1) | gold-ochre front tabard |
| BH_Gold (0.9, 0.64, 0.2) metallic | hems, hood trim/band/ridge, halo, cuirass rims + sun boss, pauldron rims, bracers, shield rim + lattice + studs, mace bands/core/pommel |
| BH_Steel (0.86, 0.85, 0.8) metallic 0.55 | pale cuirass, domed pauldrons, mace haft + flanges |
| BH_Skin / BH_Shadow | face / hood interior, sockets |
| BH_Leather (tan) | belt, boots, gloves, grips, shield strap |
| BH_Wood | shield core edge |
| BH_Emissive (1.0, 0.72, 0.28) x8 | the arched lantern-window in the shield centre, halo inner band, chest sun-boss heart, hood-brow sun, eyes |

## What makes it distinct
The only white-robed enemy. Silhouette: tall kite shield (1.08 m) carried in front on the left, a spiked gold sun-halo standing behind a tall rounded hood, domed shoulder caps and a flanged mace. At the gameplay camera it reads as a white figure with a gold ring over its head and a big pale shield with a warm glowing window. Versus the mirror knight (sandstone plate, round mirror shield, helm) it is cloth-robed, hooded and haloed with a pointed kite shield; versus the other casters it is the only one with a shield.

## Evidence
- `aegis_acolyte_rest_iso.png`: T-pose front/back, idle_shield at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `aegis_acolyte_clips.png`: idle_shield, every attack clip, hit_heavy, death_back.
- `logs/aegis_acolyte_metrics.json`: worst absolute edge growth 0.068 m (death_crumple, hood edge at the neck); idle_look / death_fwd 0.053 m (hood base over the neck).
- `logs/godot_check_aegis_acolyte.txt`: scratch Godot 4.7.2 project, 0 import errors, all 47 clips present with the meta lengths, `block_loop` keeps its name; loops applied at runtime from the meta.

## Build log
```
[aegis_acolyte] mesh 14902 tris, 156 parts, 1.0s
[aegis_acolyte] baked 47 actions in 19.4s
00:45:48 | INFO: Finished glTF 2.0 export in 3.3284566402435303 s
[aegis_acolyte] clip lengths verified (47 clips)
[aegis_acolyte] -> A:\Python\beyond-heroes\game\assets\characters\aegis_acolyte.glb (3.2 MB)
[build] done in 24.1s
```

## Revision passes
1. The first hood was a tall white cone with a face opening, which read as an unwanted real-world hate-group hood. It was replaced by a rounded tall hood, and a gold sun-halo was added behind it as the head silhouette key. BH_Steel was fully metallic and rendered almost black on the large cuirass. It was lowered to metallic 0.55 / roughness 0.38 so the plate reads pale. The mace flanges had inverted winding and were fixed.

## Known limitations
- The halo floats about 8 cm behind the hood, rigid on `head`. In deep bows (death_crumple, knockdown) it passes through the upper back / cape area briefly.
- The generic cast clips (`cast_quick`, `cast_area`) lower the shield arm; the shield swings wide during them.
- Shield face is single material white with a gold rim; no heraldic painting beyond the window and studs.
