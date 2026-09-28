# Mirror Knight (`mirror_knight`)

Built by Builder B1 (warriors); evidence written by Builder B2 (B1 was cut off before writing it). Not rebuilt.

- Module: `tools/blender/characters/enemy_mirror_knight.py` (knight plate kit `char_knight` via `enemy_hollow_soldier.Scaled`)
- GLB: `game/assets/characters/mirror_knight.glb` (3.3 MB, built 23:02) + `mirror_knight.glb.import`
- Triangles: 17578 (budget 20k); 24 bones; 8 materials
- Height: ~2.2 m to the helm finial (T-pose top 2.225 m, idle_shield f0 2.211 m; standard skeleton x 1.08)
- Clips (47): the shared enemy base clips + `sword_1 sword_2 sword_heavy shield_bash taunt war_cry` (`taunt` is already in the base set, hence 47 not 48)
- Weapons: curved sabre with gold knuckle bow on `weapon.R`; large round mirror shield on the left arm (face -Y). Stance clip: `idle_shield`.

## Palette (`mirror_knight`, exported as `BH_*__mirror_knight`)
| material | use |
|---|---|
| BH_Steel (0.8, 0.68, 0.46) metal 0.9 | pale sandstone-gold plate |
| BH_Bronze (0.86, 0.88, 0.92) metal 1.0 rough 0.16 | polished silver trim, sabre |
| BH_Gold | shield rim, knuckle bow |
| BH_Aether (0.92, 0.94, 0.98) rough 0.1, faint pale emission | mirror: shield face and the faceless visor |
| BH_DarkSteel | mail, under-plates |
| BH_Cloth_Primary / Secondary | sand tabard / brown border |
| BH_Leather, BH_Shadow | straps, gaps |

## What makes it distinct
The only enemy with a huge bright mirror disc on the arm and a faceless mirrored sugarloaf helm: at the gameplay
camera the shield reads as a pale bright circle half the knight's height. Warm sand-gold plate is unlike the dark
iron of the frost revenant / hollow soldiers and the black plate of the soulbound twin.

## Evidence
- `mirror_knight_rest_iso.png`: T-pose front/back, idle_shield at 4 yaws, helm close-ups, gameplay camera 54 deg at 16 / 22 m (re-rendered by B2 from the module).
- `mirror_knight_clips.png`: every attack clip at 5 frames (B1's render, 23:02, same build).
- `logs/mirror_knight_metrics.json`: worst absolute edge growth 0.11 m (run, upper thigh at the tasset edge).
- `logs/godot_check_warriors.txt`: scratch Godot 4.7.2 project (`scratch/brutes/godot_warriors`), 0 import errors, all 47 expected clips present with the `anim_meta.json` lengths.

## Build log
```
[mirror_knight] mesh 17578 tris, 129 parts, 1.7s
[mirror_knight] baked 47 actions in 21.5s
23:02:51 | INFO: Finished glTF 2.0 export in 4.27 s
[mirror_knight] clip lengths verified (47 clips)
[mirror_knight] -> A:\Python\beyond-heroes\game\assets\characters\mirror_knight.glb (3.3 MB)
```

## Known limitations
- `mirror_knight.glb.import` has since been re-imported by the Orchestrator (has a `uid`) with `nodes/use_name_suffixes=true`, so `block_loop` imports as `block` (loop). Same as most existing enemies; the check accepts that alias.
- The module file is dated two minutes after the GLB (23:04 vs 23:02). Triangle count of a module build (metrics run) matches the GLB (17578); if the change was more than cosmetic, a rebuild is needed to pick it up.
- The mirror is a bright material, not a real reflection.
- Tasset / upper thigh stretch in run is the largest deformation (0.11 m); plate parts overlap a little at full stride.
