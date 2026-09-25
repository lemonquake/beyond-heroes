# Contract: characters, animation library, weapons (bh-001 / C3)

Build with Blender 5.2.1 Python scripts only (`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python <script>`).
All scripts live in `tools/blender/characters/` and must regenerate every output from scratch (deterministic; no manual edits).
Outputs go to `game/assets/characters/` and `game/assets/weapons/`. Do not touch any other folder, and do NOT run Godot on
the main project (`game/`). You may run Godot on a throwaway project inside your scratch folder if you want to verify an import.

Art direction: dark, atmospheric high fantasy (Diablo II mood, original designs). Stylized-realistic proportions (not chibi),
readable silhouettes from an elevated isometric camera ~14 m away at 40 deg FOV. Worn steel, dark leather, deep cloth
colors, gold/bronze trim. Characters must NOT look like piles of primitives: bevels, tapered limbs, layered armor plates,
pauldrons, belts, straps, visor slits, hood folds, robe panels, etc. Budget per character 6k–18k triangles (boss up to 30k).

## Coordinate and scale conventions

- Meters. Origin at ground between the feet. Character faces **-Y in Blender** (so it faces **+Z in Godot** after glTF export, Y-up).
- Human height ~1.8 m (Knight 1.85 incl. helm). No object-level scale on export (apply transforms).
- One armature object named `Armature` per file, one or more skinned meshes. Export glTF binary (`.glb`) with animations,
  `export_yup=True`, apply modifiers, include only one armature, no cameras/lights.

## Skeleton (identical bone names, hierarchy, and rest orientations on every humanoid)

```
root
 └ hips
    ├ spine ─ chest ─ neck ─ head
    │          ├ shoulder.L ─ upper_arm.L ─ forearm.L ─ hand.L ─ weapon.L
    │          └ shoulder.R ─ upper_arm.R ─ forearm.R ─ hand.R ─ weapon.R
    ├ thigh.L ─ shin.L ─ foot.L ─ toe.L
    └ thigh.R ─ shin.R ─ foot.R ─ toe.R
```
Optional extra bones allowed per character (e.g. `cape.1`, `cape.2`, `jaw`) but the list above must exist with those exact names.
`weapon.R` / `weapon.L` are socket bones: head at the center of the grip in the closed fist, bone pointing along the direction a held
sword blade would point in the rest pose. Rigid or smooth skinning are both fine; joints must not visibly tear at extreme poses.
Rest pose: A-pose or T-pose, but identical across all humanoids so one action set retargets. Animations are authored once as Blender
actions on this skeleton and baked into every character file.

## Animation library (names are exact; every humanoid file contains all of them)

In-place animations (no root translation except vertical hips bob / crouch). Frame rate 30 fps. Use proper anticipation,
overshoot, follow-through, weight shifts, and eased interpolation; hit contact must be a clearly readable key pose.

Locomotion / idles (looping): `idle`, `idle_combat` (1H + shield/offhand ready), `idle_2h`, `idle_staff`, `idle_bow`, `idle_dual`,
`walk`, `run`, `block_loop`, `cast_channel`, `charge_hold`, `bow_draw_hold`.
One-shots: `dodge_roll`, `blink`, 
`sword_light_1`, `sword_light_2`, `sword_light_3`, `sword_heavy`,
`gs_light_1`, `gs_light_2`, `gs_heavy`,
`axe_light_1`, `axe_light_2`, `axe_heavy`,
`spear_light_1`, `spear_light_2`, `spear_heavy`,
`dagger_light_1`, `dagger_light_2`, `dagger_light_3`, `dagger_heavy`,
`dual_light_1`, `dual_light_2`, `dual_light_3`, `dual_heavy`,
`bow_release`, `staff_light_1`, `staff_light_2`, `staff_heavy`, `wand_light_1`, `wand_light_2`,
`cast_short`, `cast_long`, `cast_aoe`, `shield_bash`, `whirlwind` (loopable spin), `leap_slam`, `war_cry`,
`block_impact`, `parry`, `hit`, `stagger`, `knockback` (thrown backwards, lands on back), `getup`, `death`,
`boss_slam`, `boss_sweep`, `boss_roar`, `boss_charge` (loop), `boss_summon`.

Walk cycle ground speed ~1.6 m/s, run cycle ~5.0 m/s (measure from stride length / cycle time and report actual values; feet must not
slide when played at that speed). Attack light swings 0.45–0.75 s, heavies 0.9–1.4 s at 1.0x.

## Required metadata sidecar

`game/assets/characters/anim_meta.json`:
```json
{
  "fps": 30,
  "animations": {
    "sword_light_1": {"length": 0.6, "loop": false, "hits": [[0.22, 0.32]], "cancel_after": 0.45},
    "walk": {"length": 1.0, "loop": true, "ground_speed": 1.6, "footsteps": [0.0, 0.5]},
    "...": {}
  }
}
```
- `hits`: time windows (seconds at 1.0x) in which the weapon/spell is visibly at the contact arc. Must match the keyed poses.
- `cancel_after`: earliest time the next combo input may interrupt (recovery start).
- `footsteps`: foot-contact times for walk/run/dodge (used for audio).
- `release`: for cast/bow/throw animations, the moment the projectile/spell should spawn (seconds).

## Character files (all share the skeleton + animation set)

| File | Design |
| --- | --- |
| `knight.glb` | Hero. Full plate over mail, great helm with visor slit and crest, layered pauldrons, gauntlets, tabard with emblem shape (deep crimson `BH_Cloth_Primary`), belt with pouches, short cape (cape bones optional). |
| `mage.glb` | Hero. Hooded long coat/robe (deep indigo `BH_Cloth_Primary`) with split front panels over trousers and boots, shoulder mantle, belt with tomes/vials, face in hood shadow with faint glowing eyes (`BH_Emissive`), bracers, rune trim. |
| `hollow_soldier.glb` | Skeletal undead soldier: ribcage, skull with jaw, rusted partial armor, torn cloth. |
| `bonewarden.glb` | Heavily armored undead shield warrior: full rusted plate, horned helm. |
| `grave_archer.glb` | Lean skeletal archer with hood and quiver. |
| `ashen_cultist.glb` | Robed cultist, masked face, ember-glow sigils (`BH_Emissive`), ragged sleeves. |
| `ghoul_brute.glb` | Hulking bloated ghoul, same skeleton but ~2.4 m tall with massive shoulders/arms, hunched; bone lengths may differ, rest orientations must match. |
| `shade_stalker.glb` | Lean shadow assassin, wrapped cloth, long blades on forearms, hooded, semi-spectral (`BH_Shadow` material). |
| `boss_warden.glb` | Boss "Morthar, the Hollow Warden": corrupted colossal knight ~4.2 m tall, broken crown/horns, cracked armor leaking dark light (`BH_Emissive`), glowing rune weak point on the back (separate material `BH_WeakPoint`), tattered cape. Carries its greatmaul as part of the mesh. |

Material names are a contract (Godot overrides them): `BH_Steel`, `BH_DarkSteel`, `BH_Gold`, `BH_Leather`, `BH_Cloth_Primary`,
`BH_Cloth_Secondary`, `BH_Skin`, `BH_Bone`, `BH_Rust`, `BH_Emissive`, `BH_Shadow`, `BH_WeakPoint`, `BH_Wood`, `BH_Hair`.
Give each a sensible base color / metallic / roughness in Blender too (so the GLB looks right standalone). Vertex-level
variation or baked AO in vertex colors is welcome.

## Weapons (`game/assets/weapons/<name>.glb`)

`sword`, `greatsword`, `axe`, `spear`, `dagger`, `bow`, `staff`, `wand`, `shield` (kite/heater shield with emblem), plus
`arrow` (projectile mesh). Origin at the grip center (shield: at the arm strap/handle; arrow: at its center). Long axis along
**Blender +Z** (blade/shaft points up, pommel down). Sword flat faces ±Y, edges ±X. Shield face points -Y. Keep weapons
distinct in silhouette; staff with a crystal head (`BH_Emissive`), wand slender with a gem, bow recurve with string.
Scale: sword 1.0 m, greatsword 1.6 m, axe 0.8 m, spear 2.2 m, dagger 0.4 m, bow 1.3 m, staff 1.8 m, wand 0.35 m, shield 0.9 m tall.

## Evidence to return

1. Preview renders (EEVEE, 1024px) in `work/lemondev/bh-001/evidence/characters/`: each character front + 3/4 view; contact sheet of
   key poses for every attack animation at its hit time; walk/run contact sheet; each weapon.
2. Validation script output: every GLB re-imported into a fresh Blender scene lists its bones, animations (count + names), triangle
   count, materials; asserts the full skeleton and animation list exist. Save as `work/lemondev/bh-001/evidence/characters/validation.txt`.
3. `anim_meta.json` with measured walk/run ground speeds.
4. A README in `tools/blender/characters/` with the regeneration command.
