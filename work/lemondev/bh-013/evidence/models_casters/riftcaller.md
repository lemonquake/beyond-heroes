# Riftcaller (`riftcaller`)

- Module: `tools/blender/characters/enemy_riftcaller.py` (kits: `enemy_bandit_cutthroat` SB, `enemy_ashen_cultist` robe/hood, `kit_a_common`, `kit_e_orrery` specks/stars/domes, `char_knight` cape bones + cape secondary motion)
- GLB: `game/assets/characters/riftcaller.glb` (3.4 MB) + `riftcaller.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 12606 (budget 20k); 26 bones (24 + `cape.1`, `cape.2`); 7 materials
- Height: ~2.0 m to the cowl crown (SCALE = 2.0 / 1.87); the split cowl points rise to 2.2 m (T-pose top 2.197 m, idle f0 2.175 m); shoulder spikes to ~1.75 m
- Clips (48): the 42 shared enemy base clips + `cast_quick cast_area cast_heavy cast_ultimate boss_summon blink`
- No weapon: both hands are open gloved casting hands (nothing on weapon.R / weapon.L)

## Palette (`riftcaller`, exported as `BH_*__riftcaller`)
| material | use |
|---|---|
| BH_Cloth_Primary (0.022, 0.018, 0.03) | black robe, cowl, cape outside |
| BH_Cloth_Secondary (0.16, 0.035, 0.25) | deep-violet tabard, trims, forearm wraps |
| BH_Stone (0.02, 0.03, 0.10) | cape inner lining (dark-blue star field) |
| BH_DarkSteel (0.07, 0.05, 0.10) metallic | angular shoulder plates + spikes, clasps |
| BH_Leather | gloves, forearm bands, boots, belt |
| BH_Shadow (0.012, 0.004, 0.02) | the void inside the cowl |
| BH_Emissive (0.82, 0.3, 1.0) x10 | violet star points in the void, cape-lining stars, forearm sigils/rings, rift seam on the tabard, plate seams |

## What makes it distinct
Silhouette: a cowl split at the crown into two tall swept points (a horned "V", not the necromancer's rib fan or the void seer's single peak), big angular shoulder plates with three swept spikes each, no staff (empty casting hands), and a wide torn cape that flares at the sides. Glow: starry void face instead of eyes, a jagged glowing rift seam down the violet tabard, glowing forearm rings. The inner cape lining is a dark-blue star field that shows from the front at the cape edges and when the cape flares (run / casts).

## Evidence
- `riftcaller_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `riftcaller_clips.png`: idle, every attack clip, run (cape flare), hit_heavy, death_back.
- `logs/riftcaller_metrics.json`: worst absolute edge growth 0.083 m (death_crumple, hood trim at the face opening); run 0.078 m (cape corner at the shoulder).
- `logs/godot_check_riftcaller.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 clips present with the meta lengths, `block_loop` keeps its name; loops applied at runtime from the meta.

## Build log
```
[riftcaller] mesh 12606 tris, 192 parts, 1.0s
[riftcaller] baked 48 actions in 20.5s
23:14:35 | INFO: Finished glTF 2.0 export in 3.7164270877838135 s
[riftcaller] clip lengths verified (48 clips)
[riftcaller] -> A:\Python\beyond-heroes\game\assets\characters\riftcaller.glb (3.4 MB)
[build] done in 25.5s
```

## Revision passes
1. Cape-lining stars showed through the outside of the cape (they were computed from an already-scaled copy of the lining, i.e. scaled twice); fixed, and the octahedron specks replaced by flat discs / 4-point stars lying on the lining.

## Known limitations
- The cape is two single-sided sheets (black outside, star lining inside); seen exactly edge-on it is paper-thin. Godot's default back-face culling is what keeps the two colours apart.
- Overall very dark by design (black / deep violet); readability at distance relies on the silhouette and the violet emissives.
- Shoulder spikes are rigid on the shoulder bones; in extreme overhead casts (boss_summon, cast_ultimate) the inner spike passes close to the cowl points.
