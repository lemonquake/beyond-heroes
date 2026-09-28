# Gravecaller (`gravecaller`)

- Module: `tools/blender/characters/enemy_gravecaller.py` (kits: `enemy_bandit_cutthroat` SB, `enemy_ashen_cultist` robes, `kit_a_common`, `enemy_hollow_soldier` ragged/cloth weights)
- GLB: `game/assets/characters/gravecaller.glb` (3.8 MB) + `gravecaller.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 19998 (budget 20k); 24 bones; 10 materials
- Height: ~1.95 m to the top of the stag-skull headdress (stooped, head carried forward); antler tips 2.59 m (T-pose top incl. antlers 2.586 m, idle f0 2.574 m). SCALE = 1.95 / 1.835 of the standard skeleton.
- Clips (48): the 42 shared enemy base clips + `staff_1 staff_heavy cast_quick cast_area cast_heavy boss_summon`
- Weapon: ribcage staff rigid on `weapon.R` (library staff clips); left hand empty/open

## Palette (`gravecaller`, exported as `BH_*__gravecaller`)
| material | use |
|---|---|
| BH_Cloth_Primary (0.47, 0.45, 0.39) | bone-white grave-linen under-robe, bell sleeves |
| BH_Cloth_Secondary (0.085, 0.15, 0.055) | moss-green over-robe, back drape, shoulder capelet, sash, trims |
| BH_Skin (0.33, 0.34, 0.33) | grey dead skin (face, hands) |
| BH_Bone (0.74, 0.71, 0.62) | stag skull headdress, vertebrae mantle, staff ribcage, charms |
| BH_Horn (0.40, 0.34, 0.25) | antlers, lank hair |
| BH_Wood (0.20, 0.18, 0.15) | weathered grey crooked staff |
| BH_Fur (0.05, 0.10, 0.03) | moss rags hanging from the antlers |
| BH_Leather / BH_Shadow | cords, boots / sockets |
| BH_Emissive (0.35, 1.0, 0.5) x9 | green soul-flame in the staff cage, eyes, skull-charm eyes |

## What makes it distinct
Silhouette: tall, narrow, upright antlers (not the orc shaman's wide spread) over a bleached stag skull whose snout juts over the brow; a wide shoulder capelet laid with rows of vertebrae (dangling strands); long crooked staff with a ribcage cage and a green flame. Palette: the only robed caster that is mostly bone-white with moss green (necromancer = black/violet, void seer = midnight/brass, brinecaller = sea green, rootweaver = bark brown with no robe). Green soul-flame differs from the rootweaver's yellow-green (cooler, mint green).

## Evidence
- `gravecaller_rest_iso.png`: T-pose front/back, idle_staff at 4 yaws, head close-ups, gameplay camera (54 deg pitch, 40 deg vFOV) at 16 m / 22 m.
- `gravecaller_clips.png`: idle_staff, every attack clip, hit_heavy, death_back at 5 normalized times (Workbench).
- `logs/gravecaller_metrics.json`: deformation audit over every frame of every exported clip. Worst absolute edge growth 0.067 m (strafe_r, robe at the waist side); staff_1 / staff_heavy 0.058 m (sleeve at the shoulder). (Pass 3 fix: the back drape shares the leg influence equally between both thighs; before that the drape tore 0.22 m down the middle in run.)
- `logs/godot_check_gravecaller.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 clips present with the meta length, `block_loop` keeps its name. Loop modes are applied at runtime from the meta (character_visual._prepare_animations); imported loop flag is set only on `block_loop`.

## Build log
```
[gravecaller] mesh 19998 tris, 615 parts, 1.8s
[gravecaller] baked 48 actions in 19.9s
23:07:40 | INFO: Finished glTF 2.0 export in 3.993851661682129 s
[gravecaller] clip lengths verified (48 clips)
[gravecaller] -> A:\Python\beyond-heroes\game\assets\characters\gravecaller.glb (3.8 MB)
[build] done in 26.0s
```

## Revision passes
1. First build 36k tris (vertebrae mantle far too dense, read as chain mail) -> strands halved, simpler vertebrae; over-robe re-cut so the bone-white under-robe shows down the front.
2. Vertebrae read as spikes -> processes angled down the strand, side wings, a cord through each strand; tris trimmed to 19998.
3. Deformation: back drape reweighted (see above).

## Known limitations
- At exactly 19998 triangles there is no headroom left; any addition needs a cut elsewhere.
- The wearer's face sits in the shadow of the skull snout; its green eyes are small and do not read at gameplay distance (the staff flame and antlers carry the read).
- Staff (rigid on weapon.R) dips below the ground while lying in death/getup and in the cast_area crouch (shared library pose, same as the necromancer).
