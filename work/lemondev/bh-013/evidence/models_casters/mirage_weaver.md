# Mirage Weaver (`mirage_weaver`)

- Module: `tools/blender/characters/enemy_mirage_weaver.py` (kits: `enemy_bandit_cutthroat` SB + `curved_knife`, `enemy_ashen_cultist` skirt panels/weights, `kit_a_common`, `kit_e_orrery` discs/rings)
- GLB: `game/assets/characters/mirage_weaver.glb` (3.5 MB) + `mirage_weaver.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 18136 (budget 20k); 24 bones; 8 materials
- Height: 1.83 m to the top of the headscarf (T-pose top 1.833 m, idle f0 1.82 m); SCALE = 1.85 / 1.845, slender (shoulder_x 0.165, hip_x 0.088)
- Clips (48): the 42 shared enemy base clips + `dual_1 dual_2 dual_heavy cast_quick cast_area blink`
- Weapons: one curved dagger rigid on each of `weapon.R` and `weapon.L` (blade ~0.36 m, curved back toward the spine side). Best idle stance: `idle_dagger`.

## Palette (`mirage_weaver`, exported as `BH_*__mirage_weaver`)
| material | use |
|---|---|
| BH_Cloth_Primary (0.56, 0.40, 0.17) | sand-gold silk: headscarf + tail, shoulder shawl, over-skirt |
| BH_Cloth_Secondary (0.02, 0.27, 0.27) | teal silk: bodice, puffed sleeves, wide trousers, sash + tails, veil, head band |
| BH_Steel (0.92, 0.93, 0.95) metallic 1, roughness 0.1 | mirror discs (shawl, skirt hem, sash tails), mirror coins, dagger blades |
| BH_Gold | coin chains, bangles, anklets, trims, dagger guards |
| BH_Skin / BH_Hair / BH_Leather | skin / kohl eye sockets / sandal-boots, grips |
| BH_Emissive (1.0, 0.5, 0.82) x7 | rose shimmer: eyes, brow jewel, sash jewel, dagger pommels |

## What makes it distinct
The only sand-gold + teal enemy; not robed to the floor: knee-length over-skirt over wide ballooning trousers gathered at the ankle, a pointed shawl over the shoulders, a wound headscarf with a long tail and a teal veil over the face (eyes only), and a curved dagger in each hand. Versus the shade stalker (black wraps, dual daggers) the whole palette and silhouette are different (bright silks, wide trousers, scarf); versus the astral duelist (starglass + silver, rapier) it has two short curved blades and cloth instead of armour. Many small mirror discs / coins give sparkles when lit.

## Evidence
- `mirage_weaver_rest_iso.png`: T-pose front/back, idle_dagger at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `mirage_weaver_clips.png`: idle_dagger, every attack clip, run, hit_heavy, death_back.
- `logs/mirage_weaver_metrics.json`: worst absolute edge growth 0.058 m (dual_2, sleeve at the shoulder; over-skirt front at the crotch in wall_impact).
- `logs/godot_check_mirage_weaver.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 clips present with the meta lengths, `block_loop` keeps its name.

## Build log
```
[mirage_weaver] mesh 18136 tris, 237 parts, 1.7s
[mirage_weaver] baked 48 actions in 18.9s
23:20:19 | INFO: Finished glTF 2.0 export in 3.552044153213501 s
[mirage_weaver] clip lengths verified (48 clips)
[mirage_weaver] -> A:\Python\beyond-heroes\game\assets\characters\mirage_weaver.glb (3.5 MB)
[build] done in 24.5s
```

## Revision passes
1. The veil stood off the face as a flat slab and the nose poked through it -> the veil now wraps round the cheeks, nose removed under it; the crown of the scarf lowered with a knot at the back.

## Known limitations
- The mirror discs are true mirrors (metallic 1, roughness 0.1): in the Workbench previews and in dark scenes without reflections they read dark; they only sparkle where the environment gives them something to reflect. If they read too dark in game, raise roughness (0.25-0.3) in the palette.
- The daggers are short; at gameplay distance the dual-blade read comes mostly from the arm poses.
