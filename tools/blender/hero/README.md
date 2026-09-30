# The player's hero (bh-023)

The hero is one customisable body, built from the player's own model (`models/generic_body*`), that every class
wears gear on. Everything in `game/assets/characters/hero.glb` and `game/assets/characters/hero/` is generated here.

```sh
B="C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
"$B" -b --factory-startup --python tools/blender/hero/hero_body.py -- export   # hero.glb, hero_meta.json (~70 s)
python tools/blender/hero/hero_skin.py                                           # hero_skin.png, hero_masks.png
"$B" -b --factory-startup --python tools/blender/hero/hero_hair.py -- all      # hero/hair/*.glb, hero/beard/*.glb
"$B" -b --factory-startup --python tools/blender/hero/hero_wear.py -- all      # hero/wear/*.glb (worn equipment)
# previews (work/lemondev/bh-023/scratch): hero_body.py -- preview | shapes | retarget
```

| file | role |
|---|---|
| `hero_src.py` | reads the source GLB (mesh, weights, Tripo rig) into numpy |
| `hero_conform.py` | scales the figure to 1.80 m and carries it onto the shared skeleton's rest pose; curls the hands into fists |
| `hero_shapes.py` | landmarks, the shape keys behind the creator's sliders, the shader attributes (UV2, COLOR) |
| `hero_retarget.py` | the five source clips (walk, run, casual walk, alert, axe smash) on the shared skeleton |
| `hero_export.py` | `hero.glb`: body + shape keys + the whole action library (`tools/blender/characters`) + the source clips |
| `hero_skin.py` | skin detail texture and region masks from `models/generic_body.jpg` |
| `hero_hair.py` | hair and beard models |
| `hero_wear.py` | worn equipment, skinned to the shared skeleton and following the body's shape keys |

## Space and measurements

Blender model space of the standard skeleton (`tools/blender/characters/bh_skeleton.py`, `proportions()` unchanged):
metres, Z up, the hero faces **-Y**, the hero's left is **+X**, feet on z = 0, exact T-pose (arms along X at
z = 1.44, legs straight down at x = +-0.10).

Head (rigid, follows bone `head`, joint at (0, 0, 1.60)): top of the skull z = 1.80; width x = +-0.078 at the temples
(ears reach +-0.095); depth y = -0.145 (brow) .. +0.064 (back of the skull), so the skull's centre is about
(0, -0.04, 1.70). Eyes (+-0.0335, -0.128, 1.687); brows z = 1.708; nose tip (0, -0.160, 1.653); mouth (0, -0.143,
1.616), half width 0.029; chin (0, -0.128, 1.577); ears meet the skull at (+-0.083, -0.040, 1.666) and span
z = 1.637..1.695. The hairline is `hero_skin.hairline(y)`: 1.754 at the forehead, 1.712 at the temples, 1.668 behind
the ears, 1.61..1.63 at the nape.

Body (measured on the conformed surface): shoulder joints (+-0.19, 0, 1.44), elbows x = +-0.47, wrists x = +-0.73.
Trunk half width / front y / back y: 0.235 / -0.09 / +0.095 at z = 1.47 (shoulders), 0.168 / -0.135 / +0.096 at
z = 1.32 (chest), 0.132 / -0.136 / +0.062 at z = 1.18 (waist), 0.176 / -0.141 / +0.102 at z = 1.06, 0.21 / -0.13 /
+0.07 at z = 0.88 (hips); crotch z = 0.82. Neck half width 0.06 at z = 1.56 (y -0.11 .. +0.044).
Arms: upper arm radius ~0.06 around z = 1.44, forearm ~0.05 around z = 1.46, wrist ~0.03; the fist spans
x = 0.741..0.844, y = -0.085..+0.046, z = 1.382..1.478. Legs: thigh radius ~0.077 around x = 0.107 at z = 0.70,
knee z = 0.51 (x 0.045..0.155), shin radius ~0.05 (centred y = +0.04: the calf), ankle z = 0.10,
foot x = 0.05..0.216, y = -0.186 (toes) .. +0.084 (heel).

`work/lemondev/bh-023/scratch/hero_mesh.npz` (written by the export) holds the exact surface for fitting: `V` (n, 3),
`T` (m, 3) triangles, `N` vertex normals, `UV`, `bones` + `W` (n, bones) skin weights, `keys` + `deltas` (k, n, 3)
shape-key displacements.

## Conventions the game relies on

* `hero.glb`: material `BH_HeroSkin` (replaced by `res://src/actors/hero/hero_skin.gdshader`); UV2 = rest (x, z),
  COLOR.r = front of the head, COLOR.g = rest y packed as (y + 0.32) / 0.64.
* Hair / beard GLBs: one mesh in model space (not moved to the head joint), material `BH_HeroHair`, vertex colour
  R = how freely that vertex sways (0 at the scalp, 1 at the tips), optional shape key `length`.
* Worn equipment GLBs: meshes skinned to the shared bone names, materials `<BH base>__it_<key>` as the item models
  use, shape keys `muscle`, `belly`, `build`, `rear` copied from the body so clothing follows the body sliders.
