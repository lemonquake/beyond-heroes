# ilsa — Captain Ilsa Rhondar of the Sunwake (bh-029, Builder N1)

- Module: `tools/blender/characters/town_ilsa.py` (palette `town_ilsa`, `TINTABLE = ("BH_Cloth_Primary",)`,
  `CLIPS_ONLY = TOWN_CLIPS`)
- GLB: `game/assets/characters/ilsa.glb` + `ilsa.glb.import` (copied from officer.glb.import, paths re-hashed, no uid=)
- Build: `cd tools/blender/characters && blender -b --factory-startup --python build.py -- ilsa`
- Game wiring: `DataNpcsZarael._m("ilsa", ...)` resolves `res://assets/characters/ilsa.glb` (previous fallback: fisher).
  NPC tint: (0.22, 0.32, 0.4) sea blue -> long coat + collar + sleeves.
- Triangles: 9218 (budget 15k). Verts: 4795.
- Height: T-pose top 1.771 m, idle top 1.759 m (includes headgear / props).
- Glow: none

## Look
Weathered sea captain: long sea-blue coat (tinted) to mid-calf, tall turned collar, dark lapel facings, two rows of brass buttons, dark hems, wide dark cuffs with a brass button; cream shirt, red neckerchief; wide ochre sash knotted at the right-back hip under a leather belt with brass buckle; short curved sword in a leather scabbard at the left hip (shell guard); brass three-draw spyglass in a holster at the right hip; dark breeches and folded-top sea boots; brown hair with two grey streaks swept back, long braid down the back tied with red; gold hoop earring (right ear).

## Materials
BH_Cloth_Secondary__town_ilsa,BH_Cloth_Red__town_ilsa,BH_Cloth_Primary,BH_Cloth_Dark__town_ilsa,BH_Gold__town_ilsa,BH_Skin__town_ilsa,BH_Cloth_Accent__town_ilsa,BH_Leather__town_ilsa,BH_Wood__town_ilsa,BH_Shadow__town_ilsa,BH_Hair__town_ilsa,BH_HairGrey__town_ilsa

## Godot import (scratch project work/lemondev/bh-029/scratch/n1/proj, Godot 4.7.2 headless)
```
GLB ilsa tris=9218 bones=24 mats=12 anims=6 expected=6 missing=[] length_mismatch=[]
CLIPS ilsa idle:4.000:none idle_adjust:4.000:none idle_look:4.000:none interact_pickup:1.000:none interact_talk:3.000:none walk:0.867:none
```
Loop modes are `none` exactly like officer/elder (same import settings); CharacterVisual sets loop modes from anim_meta at load (character_visual.gd:177).

## Deformation (Blender, evaluated mesh vs rest; stretch ratio of the worst edge, absolute growth in m)
| clip | frames | max stretch (bone) | abs grow | min z |
|---|---|---|---|---|
| idle | 121 | 2.324 (shoulder.L) | 0.042 | -0.0 |
| idle_adjust | 121 | 2.369 (shoulder.R) | 0.05 | -0.0 |
| idle_look | 121 | 2.324 (shoulder.L) | 0.042 | -0.0 |
| interact_pickup | 31 | 2.553 (shoulder.R) | 0.092 | -0.0 |
| interact_talk | 91 | 2.324 (shoulder.R) | 0.042 | -0.0 |
| walk | 27 | 2.36 (shoulder.R) | 0.066 | -0.004 |

Reference: existing town_elder walk 5.02 / abs 0.195 / zmin -0.051; officer walk 3.79 (same shoulder-edge baseline ~2.3).

## Build log
```
[ilsa] inward part collar (102 faces)
[ilsa] mesh 9218 tris, 79 parts, 1.1s
[ilsa] baked 6 actions in 6.2s
[ilsa] clip lengths verified (6 clips)
[ilsa] -> A:\Python\beyond-heroes\game\assets\characters\ilsa.glb (1.1 MB)
[build] done in 8.9s
```

## Evidence
- `ilsa_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 m / 22 m.
- `ilsa_clips.png`: idle_look, interact_talk, walk, interact_pickup at 4 times each.

## Known limitations
No glow on this model (none needed; palette is in the white-glow list anyway). The check_normals heuristic flags the flared collar, but its signed volume is positive (outward) after the flip.
Workbench previews only (material colours; BH_Cloth_Primary shows the preview colour, the game tints it).
