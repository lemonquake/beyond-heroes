# Treasure Mimic (treasure_mimic.glb)

Generator: `tools/blender/creatures/build_mimic.py` -> `game/assets/characters/treasure_mimic.glb`

- Size: chest 1.00 m wide x 0.65 m deep x 0.75 m tall closed; awake stance lifts it 0.30 m on four legs (foot span ~1.45 m).
- Triangles: 11772; vertices 6583; bones 21 (root non-deform).
- Materials: BH_Bone__treasure_mimic, BH_DarkSteel__treasure_mimic, BH_Emissive__treasure_mimic, BH_Flesh__treasure_mimic, BH_Gold__treasure_mimic, BH_Hair__treasure_mimic, BH_Horn__treasure_mimic, BH_Leather__treasure_mimic, BH_Shadow__treasure_mimic, BH_Skin__treasure_mimic, BH_Wood__treasure_mimic
- Bones: `root`, `body`, `lid`, `tongue.0`, `tongue.1`, `tongue.2`, `tongue.3`, `tongue.4`, `tongue.5`, `thigh.FL`, `shin.FL`, `foot.FL`, `thigh.BL`, `shin.BL`, `foot.BL`, `thigh.FR`, `shin.FR`, `foot.FR`, `thigh.BR`, `shin.BR`, `foot.BR`
- Rest pose = awake stance with the lid shut. `mimic_dormant` = chest on the ground, legs scaled to 1.5 % about their roots (inside the solid box bottom), lid shut, tongue inside, no motion.
- Dormant check: leg/tongue bone points z 0.023..0.320 m, |x| <= 0.303, |y| <= 0.280 (closed box spans z 0..0.75, |x| < 0.5, |y| < 0.325).
- mimic_tongue: tongue tip reaches 3.00 m in front of the origin at frame 12 (0.40 s), 0.80 m high.

## Clips

| clip | frames | length (s) | loop | hits (s) | ground_speed (m/s) |
|---|---|---|---|---|---|
| `mimic_dormant` | 30 | 1.000 | yes | - | - |
| `mimic_wake` | 36 | 1.200 | no | - | - |
| `idle` | 60 | 2.000 | yes | - | - |
| `walk` | 14 | 0.467 | yes | - | 1.2 |
| `run` | 10 | 0.333 | yes | - | 3.2 |
| `run_combat` | 10 | 0.333 | yes | - | 3.0 |
| `hit_light` | 12 | 0.400 | no | - | - |
| `hit_heavy` | 18 | 0.600 | no | - | - |
| `stagger_small` | 24 | 0.800 | no | - | - |
| `knockback` | 27 | 0.900 | no | - | - |
| `alert` | 30 | 1.000 | no | - | - |
| `death` | 45 | 1.500 | no | - | - |
| `death_back` | 45 | 1.500 | no | - | - |
| `mimic_bite` | 24 | 0.800 | no | [0.433, 0.533] | - |
| `mimic_tongue` | 36 | 1.200 | no | [0.400, 0.500] | - |
| `mimic_slam` | 36 | 1.200 | no | [0.733, 0.833] | - |

## Foot contact (in-place clips; stance feet slide back at exactly ground_speed)

| clip | max slip mm/frame | mean slip mm/frame | stance fraction |
|---|---|---|---|
| walk | 0.00 | 0.00 | 0.57 |
| run | 0.00 | 0.00 | 0.35 |
| run_combat | 0.00 | 0.00 | 0.35 |

Worst IK reach miss per clip (mm; folded / curled legs excluded): mimic_dormant 0.0, mimic_wake 0.0, idle 0.0, walk 0.0, run 0.0, run_combat 0.0, hit_light 0.0, hit_heavy 0.0, stagger_small 0.0, knockback 0.0, alert 0.0, death 6.5, death_back 4.7, mimic_bite 0.0, mimic_tongue 0.0, mimic_slam 2.7
