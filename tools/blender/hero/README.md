# The player's hero (bh-023)

The hero is one customisable body, built from the player's own model (`models/generic_body*`), that every class
wears gear on. Everything in `game/assets/characters/hero.glb` and `game/assets/characters/hero/` is generated here.

```sh
B="C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
"$B" -b --factory-startup --python tools/blender/hero/hero_body.py -- export   # hero.glb, hero_meta.json (~70 s)
python tools/blender/hero/hero_skin.py                                           # hero_skin.png, hero_masks.png
"$B" -b --factory-startup --python tools/blender/hero/hero_hair.py -- all      # hero/hair/*.glb, hero/beard/*.glb
"$B" -b --factory-startup --python tools/blender/hero/hero_wear.py -- all      # hero/wear/*.glb (worn equipment)
# bh-031 female figure (re-run before the export above when the hero mesh or the scan changes):
"$B" -b --factory-startup --python tools/blender/hero/hero_female_src.py       # scan -> work/lemondev/bh-031/scratch/female
python tools/blender/hero/hero_female.py                                         # -> data/female_delta.npz (needs scipy)
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
| `hero_female_src.py` | bh-031: `models/female_generic.obj` (1M-vertex scan, vertex colours, no rig) decimated to numpy |
| `hero_female.py` | bh-031: the hero body fitted onto the scan (limbs conformed to the rig, shrink-wrap, a round bust) -> the `female` shape key (`data/female_delta.npz`, read by `hero_shapes.py`) |
| `hero_female_anims.py` | bh-031: `fem_idle`, `fem_walk`, `fem_stroll`, `fem_run` layered over the hero's clips (pelvis sway, counter-turned shoulders, narrower steps) |
| `hero_wear.py` | worn equipment, skinned to the shared skeleton and following the body's shape keys (`-- all`, `-- <ids>`, `-- preview <a+b+c outfits>`) |
| `hero_wear_kit.py` | shell() / attach() / build_object(), the registry (`@item`), `plate()` (worn plate material), the manifest |
| `hero_wear_torso.py` | the 16 armours and inner garments (they stop at the hips; `skirt=` records how low a skirt hangs) |
| `hero_wear_legs.py` | bh-024: the 34 leggings, `_breeches` (a clothed hero without leggings) and `_under_legs` (under boss Legguards) |
| `hero_wear_ends.py` | helms, gloves, boots and jewellery (rings on the fist, pendants on the breastbone, charms at the hip) |

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
  use, shape keys `muscle`, `belly`, `build`, `rear`, `female` copied from the body so clothing follows the body sliders.
* bh-031: `hero_src.load()` refines the chest triangles 1 -> 4 (crack-free) so the female key can hold a bust; the
  body is 5,919 vertices / 11,784 triangles.
* bh-024 mesh groups: a piece may return `{group: [WParts]}`; its GLB then holds `wear` and `wear_<group>` meshes. Leggings
  use `waist` (belt, panels, tassets), `hip` (thigh plates and guards, pouches), `knee` (knee cops and pads) and
  `ankle_L` / `ankle_R` (cuffs, low wraps); HeroWear.plan leaves a group off under a shirt, a skirt below 0.80 m, a robe
  below 0.45 m or a boot on that side. `skirt` in the manifest is the lowest height of a body garment's skirt.
* Layers: inner garments 5-9 mm, armour cloth 10-16 mm, plates beyond; leggings are tucked in at 3.5 mm under the body
  garments' hems (which stand 6.5 mm or more out) and stay within 6.5 mm below the calf so boot shafts (10-16 mm) close
  over them.
* Budgets (game/tests/unit/test_bh023.gd, test_bh024.gd): helm 1,600, inner garment 5,600, armour 8,400, leggings
  6,500, gloves 1,800 and boots 1,600 a side, jewellery 300.
