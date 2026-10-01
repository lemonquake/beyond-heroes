# agdao_porter — Agdao porters / lift engineers / scouts (Toma Kettridge, Quillan Ashby) (bh-029, Builder N1)

- Module: `tools/blender/characters/town_agdao_porter.py` (palette `town_agdao_porter`, `TINTABLE = ("BH_Cloth_Primary",)`,
  `CLIPS_ONLY = TOWN_CLIPS`)
- GLB: `game/assets/characters/agdao_porter.glb` + `agdao_porter.glb.import` (copied from officer.glb.import, paths re-hashed, no uid=)
- Build: `cd tools/blender/characters && blender -b --factory-startup --python build.py -- agdao_porter`
- Game wiring: `DataNpcsZarael._m("agdao_porter", ...)` resolves `res://assets/characters/agdao_porter.glb` (previous fallback: smith / traveler).
  NPC tint: (0.42, 0.3, 0.18) Toma, (0.3, 0.34, 0.24) Quillan -> quilted vest.
- Triangles: 9982 (budget 15k). Verts: 5258.
- Height: T-pose top 1.992 m, idle top 1.980 m (includes headgear / props).
- Glow: BH_Emissive__town_agdao_porter albedo=(1.0, 1.0, 1.0, 1.0) emission=(1.0, 1.0, 1.0, 1.0) energy=4.50

## Look
Sturdy working man: sleeveless quilted vest (tinted) nearly closed with leather front lacing, quilt ridges, red edges and a stepped-fret hem; bare muscular arms, leather wrist wraps, one thin white-glowing wire bracelet (left forearm); cream trousers wrapped ankle-to-knee with red strips; sandals; wide leather tool belt with a hammer (right), open-jawed wrench (left), two pouches; three turns of copper wire slung from the left shoulder to the right hip; woven carrying frame on the back (portrait): two poles rising above the head, tall wicker pack with weave ridges and red bands, a cream bundle lashed on top, shoulder straps; red headband with a knot and tails over short dark hair.

## Materials
BH_Skin__town_agdao_porter,BH_Cloth_Primary,BH_Cloth_Accent__town_agdao_porter,BH_Cloth_Secondary__town_agdao_porter,BH_Leather__town_agdao_porter,BH_Emissive__town_agdao_porter,BH_Gold__town_agdao_porter,BH_Wood__town_agdao_porter,BH_DarkSteel__town_agdao_porter,BH_Wicker__town_agdao_porter,BH_Shadow__town_agdao_porter,BH_Hair__town_agdao_porter

## Godot import (scratch project work/lemondev/bh-029/scratch/n1/proj, Godot 4.7.2 headless)
```
GLB agdao_porter tris=9982 bones=24 mats=12 anims=6 expected=6 missing=[] length_mismatch=[]
CLIPS agdao_porter idle:4.000:none idle_adjust:4.000:none idle_look:4.000:none interact_pickup:1.000:none interact_talk:3.000:none walk:0.867:none
```
Loop modes are `none` exactly like officer/elder (same import settings); CharacterVisual sets loop modes from anim_meta at load (character_visual.gd:177).

## Deformation (Blender, evaluated mesh vs rest; stretch ratio of the worst edge, absolute growth in m)
| clip | frames | max stretch (bone) | abs grow | min z |
|---|---|---|---|---|
| idle | 121 | 2.452 (shoulder.R) | 0.05 | -0.0 |
| idle_adjust | 121 | 2.655 (shoulder.R) | 0.06 | -0.0 |
| idle_look | 121 | 2.452 (shoulder.L) | 0.05 | -0.0 |
| interact_pickup | 31 | 2.765 (shoulder.R) | 0.058 | -0.0 |
| interact_talk | 91 | 2.452 (shoulder.R) | 0.05 | -0.0 |
| walk | 27 | 2.504 (shoulder.R) | 0.049 | -0.002 |

Reference: existing town_elder walk 5.02 / abs 0.195 / zmin -0.051; officer walk 3.79 (same shoulder-edge baseline ~2.3).

## Build log
```
[agdao_porter] mesh 9982 tris, 110 parts, 1.2s
[agdao_porter] baked 6 actions in 6.6s
[agdao_porter] clip lengths verified (6 clips)
[agdao_porter] -> A:\Python\beyond-heroes\game\assets\characters\agdao_porter.glb (1.2 MB)
[build] done in 9.4s
```

## Evidence
- `agdao_porter_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 m / 22 m.
- `agdao_porter_clips.png`: idle_look, interact_talk, walk, interact_pickup at 4 times each.

## Known limitations
Pack/frame are rigid to the chest; pole tops reach 1.99 m. The coil passes under the pack at the back.
Workbench previews only (material colours; BH_Cloth_Primary shows the preview colour, the game tints it).
