# wirekeeper — Wirekeeper Halvessa Orn (bh-029, Builder N1)

- Module: `tools/blender/characters/town_wirekeeper.py` (palette `town_wirekeeper`, `TINTABLE = ("BH_Cloth_Primary",)`,
  `CLIPS_ONLY = TOWN_CLIPS`)
- GLB: `game/assets/characters/wirekeeper.glb` + `wirekeeper.glb.import` (copied from officer.glb.import, paths re-hashed, no uid=)
- Build: `cd tools/blender/characters && blender -b --factory-startup --python build.py -- wirekeeper`
- Game wiring: `DataNpcsZarael._m("wirekeeper", ...)` resolves `res://assets/characters/wirekeeper.glb` (previous fallback: scholar).
  NPC tint: (0.2, 0.45, 0.45) teal -> long robe + sleeves + stockings.
- Triangles: 13154 (budget 15k). Verts: 6928.
- Height: T-pose top 1.835 m, idle top 1.824 m (includes headgear / props).
- Glow: BH_Emissive__town_wirekeeper albedo=(1.0, 1.0, 1.0, 1.0) emission=(1.0, 1.0, 1.0, 1.0) energy=4.50

## Look
Older woman, slightly stooped: long deep-teal robe (tinted) with brick-red fret hem band and cream steps; cream sleeveless over-robe open at the front, red edges, split skirt with red fret hem; short turquoise mosaic collar with gold rim and coral/cream/copper chips; elbow sleeves with red cuffs, bare forearms coiled with copper wire plus two faint white-glowing wire rings each; leather tool satchel (handles, bronze rule, wire coil) on a cross strap; round copper spectacles; grey hair falling at the sides and bound up in a tall knot wrapped in three copper bands with a turquoise stone and a wooden hair-stick (the portrait's banded headdress); bronze wire-gauge staff in the right hand (rigid to hand.R) wound with copper, a notched gauge ring, small white-glowing tip.

## Materials
BH_Cloth_Primary,BH_Cloth_Accent__town_wirekeeper,BH_Cloth_Secondary__town_wirekeeper,BH_Skin__town_wirekeeper,BH_Gold__town_wirekeeper,BH_Emissive__town_wirekeeper,BH_Leather__town_wirekeeper,BH_Wood__town_wirekeeper,BH_Turquoise__town_wirekeeper,BH_Coral__town_wirekeeper,BH_Bronze__town_wirekeeper,BH_Shadow__town_wirekeeper,BH_Hair__town_wirekeeper

## Godot import (scratch project work/lemondev/bh-029/scratch/n1/proj, Godot 4.7.2 headless)
```
GLB wirekeeper tris=13154 bones=24 mats=13 anims=6 expected=6 missing=[] length_mismatch=[]
CLIPS wirekeeper idle:4.000:none idle_adjust:4.000:none idle_look:4.000:none interact_pickup:1.000:none interact_talk:3.000:none walk:0.867:none
```
Loop modes are `none` exactly like officer/elder (same import settings); CharacterVisual sets loop modes from anim_meta at load (character_visual.gd:177).

## Deformation (Blender, evaluated mesh vs rest; stretch ratio of the worst edge, absolute growth in m)
| clip | frames | max stretch (bone) | abs grow | min z |
|---|---|---|---|---|
| idle | 121 | 2.308 (shoulder.L) | 0.05 | -0.019 |
| idle_adjust | 121 | 2.351 (shoulder.R) | 0.048 | -0.014 |
| idle_look | 121 | 2.308 (shoulder.L) | 0.058 | -0.018 |
| interact_pickup | 31 | 4.437 (thigh.L) | 0.231 | -0.098 |
| interact_talk | 91 | 2.308 (shoulder.L) | 0.046 | -0.012 |
| walk | 27 | 5.082 (thigh.L) | 0.236 | -0.05 |

Reference: existing town_elder walk 5.02 / abs 0.195 / zmin -0.051; officer walk 3.79 (same shoulder-edge baseline ~2.3).

## Build log
```
[wirekeeper] mesh 13154 tris, 175 parts, 1.5s
[wirekeeper] baked 6 actions in 5.6s
[wirekeeper] clip lengths verified (6 clips)
[wirekeeper] -> A:\Python\beyond-heroes\game\assets\characters\wirekeeper.glb (1.4 MB)
[build] done in 8.6s
```

## Evidence
- `wirekeeper_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 m / 22 m.
- `wirekeeper_clips.png`: idle_look, interact_talk, walk, interact_pickup at 4 times each.

## Known limitations
Long robe dips ~5-10 cm below the floor in interact_pickup (same as the existing town_elder). Gauge staff is rigid to hand.R, upright in idle/walk/talk.
Workbench previews only (material colours; BH_Cloth_Primary shows the preview colour, the game tints it).
