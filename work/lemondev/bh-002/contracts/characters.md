# Contract C6: hero characters, weapons, animation library (bh-002)

## Context

Beyond Heroes is a Godot 4.4.1 isometric action RPG (camera ~14 m away, 40–45° pitch, 40–45° FOV). The game code already
loads `res://assets/characters/<name>.glb` (AnimationPlayer + Skeleton3D) and `res://assets/characters/anim_meta.json`, and
attaches weapons to the `weapon.R` / `weapon.L` bones. bh-001 started a Blender pipeline in `tools/blender/characters/`
(`bh_math`, `bh_mesh`, `bh_body`, `bh_skeleton`, `bh_anim`, `bh_materials`, `bh_weapons`, `bh_render`, `char_knight.py`,
`build.py`, `render_previews.py`) but never finished it: `build.py` imports `build_chars` and `bh_library`, which do not exist,
and no GLB was exported. Reuse whatever is good, rewrite whatever is not. Everything must regenerate from scripts
(deterministic, no manual edits).

Blender: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup --python <script> -- <args>`.
System Python 3.12 has numpy/PIL/scipy (for composing contact sheets).

## Owned paths (do not write anywhere else)

`tools/blender/characters/**`, `game/assets/characters/**`, `game/assets/weapons/**`, `work/lemondev/bh-002/evidence/characters/**`.
Do NOT run Godot on `game/` (the orchestrator imports assets). You may run Godot 4.4.1
(`A:\Installer\Godot_v4.4.1-stable_win64.exe\Godot_v4.4.1-stable_win64_console.exe`) on a throwaway project in your scratch
folder to verify that a GLB imports with its skeleton, animations and materials.

## Art direction

"Ancient fantasy with mystical technology": heroic mythology, arcane energy, **Aether** (cyan-white luminous energy running
through engraved channels). Stylized-realistic proportions (not chibi), readable silhouettes from the isometric camera.
Worn steel, dark leather, deep cloth, bronze/gold trim, glowing aether inlays. Characters must not look like piles of
primitives: bevels, tapered limbs, layered plates, straps, cloth panels, trims. 8k–25k triangles per hero.

- **Knight** — ancient-tech warrior: layered plate armor (pauldrons in 2–3 lames, couters, poleyns, gauntlets heavier than
  the forearm), aether-powered engravings (thin emissive channels on chest plate, pauldrons, gauntlets — material
  `BH_Aether`), crimson tabard/cloth layers (`BH_Cloth_Primary`), mail skirt, belt with pouches, great helm with visor slit
  and a crest or ridge, short cape (cape bones optional). Distinctive broad-shouldered silhouette.
- **Mage** — arcane traveler: layered hooded long coat (deep indigo `BH_Cloth_Primary`) with split front panels over trousers
  and boots, shoulder mantle, light armor pieces (bracers, a chest harness, one pauldron), floating or mounted aether
  crystals (`BH_Aether`), runic trim, a belt with tomes/vials, face readable under the hood (skin `BH_Skin`, faint glowing
  eyes allowed), a magical gauntlet or focus bracelet on the off hand.

Material names are a contract (the game overrides them by name): `BH_Steel`, `BH_DarkSteel`, `BH_Gold`, `BH_Leather`,
`BH_Cloth_Primary`, `BH_Cloth_Secondary`, `BH_Skin`, `BH_Bone`, `BH_Rust`, `BH_Emissive`, `BH_Aether`, `BH_Shadow`,
`BH_WeakPoint`, `BH_Wood`, `BH_Hair`. Give each a sensible base color/metallic/roughness in Blender too. Vertex colors with
baked AO / wear are welcome (the game multiplies vertex color into albedo when present).

## Coordinates and skeleton (unchanged from bh-001; the game depends on these names)

Meters, origin at ground between the feet, character faces -Y in Blender (+Z in Godot after `export_yup=True`). One armature
object named `Armature`, apply transforms, no cameras/lights. Human height ~1.8 m (Knight ~1.88 incl. helm).

```
root
 └ hips
    ├ spine ─ chest ─ neck ─ head
    │          ├ shoulder.L ─ upper_arm.L ─ forearm.L ─ hand.L ─ weapon.L
    │          └ shoulder.R ─ upper_arm.R ─ forearm.R ─ hand.R ─ weapon.R
    ├ thigh.L ─ shin.L ─ foot.L ─ toe.L
    └ thigh.R ─ shin.R ─ foot.R ─ toe.R
```
Extra bones allowed (cape.1/cape.2, hood, crystal.*). `weapon.R`/`weapon.L`: head at the grip center in the closed fist,
bone pointing along a held blade's direction. Identical rest pose on all humanoids so one action set retargets.

## Animation library (exact names; every hero GLB contains all of them)

30 fps, in place (no root translation except vertical hips motion), eased interpolation with anticipation, overshoot,
follow-through and weight shift. Contact frames must be readable key poses. Loops must be seamless.

Idles (loop): `idle` (normal breathing), `idle_look` (looking around, ~4 s), `idle_adjust` (equipment adjustment: tugging a
gauntlet / straightening the belt, ~4 s), `idle_knight` (class personality: plants weapon, rolls shoulders), `idle_mage`
(class personality: conjures a small orb in the palm, turns it, lets it fade), `idle_hurt` (badly hurt: hunched, one hand
holding the ribs, heavy breathing).
Stance idles (loop): `idle_1h` (one-handed weapon, no shield), `idle_shield` (sword + shield raised ready), `idle_2h`
(greatsword/two-handed), `idle_spear`, `idle_dagger`, `idle_bow`, `idle_staff`, `idle_wand`, `idle_dual`, `idle_combat_hurt`
(injured combat stance).
Locomotion (loop): `walk`, `run`, `walk_back`, `strafe_l`, `strafe_r`, `run_combat` (weapon-ready run, slightly lower),
`walk_hurt`, `run_hurt` (limping). One-shots: `run_start`, `run_stop`, `turn_l`, `turn_r` (90° in place), `dodge_roll`,
`dodge_step` (short backstep/sidestep).
Basic attack chains — four attacks per weapon that chain naturally (each ends near where the next begins):
`sword_1..4`, `gs_1..4` (greatsword), `axe_1..4`, `spear_1..4`, `dagger_1..4`, `dual_1..4`, `staff_1..4`, `wand_1..4`,
`bow_1..2` (quick shots) plus `bow_draw_hold` (loop) and `bow_release`.
Heavy attacks: `sword_heavy`, `gs_heavy`, `axe_heavy`, `spear_heavy`, `dagger_heavy`, `dual_heavy`, `staff_heavy`, `wand_heavy`.
Charged: `charge_hold` (loop, weapon drawn back), `charge_release`. `special_attack` (spinning double strike used by
weapon specials).
Shield: `block_loop` (loop), `block_impact`, `parry`, `shield_bash`.
Casts: `cast_quick`, `cast_heavy`, `cast_channel` (loop), `cast_area` (both hands to the ground/up, ring), `cast_weapon`
(weapon skill raise), `cast_ultimate` (big two-hand overhead). Skills: `whirlwind` (loop spin), `leap_slam`, `war_cry`, `blink`.
Hit reactions: `hit_light`, `hit_heavy`, `hit_front`, `hit_back`, `hit_left`, `hit_right`.
Stagger / physics: `stagger_small`, `stagger_heavy`, `knockback` (thrown backwards, lands on back), `launch` (airborne
flail, loopable), `wall_impact` (slams back-first into a surface and slumps), `knockdown` (falls), `getup`, `death`, `revive`.
Interaction: `interact_pickup` (crouch and pick up), `interact_chest` (open a lid), `interact_talk` (gesture), `interact_teleport`
(raise hand, brace).
Enemy/boss (also baked into every humanoid): `alert` (startled, weapon up), `taunt`, `boss_slam`, `boss_sweep`, `boss_roar`,
`boss_charge` (loop), `boss_summon`.

Timing guidance at 1.0x: light attacks 0.45–0.75 s, 4th attack of a chain 0.7–0.95 s (finisher), heavies 0.9–1.4 s,
casts 0.5 (quick) to 1.3 s (ultimate), hit reactions 0.35–0.6 s, knockback ~1.2 s, getup ~0.9 s.
Walk ground speed ~1.6 m/s, run ~5.0 m/s, strafe ~3.2 m/s, walk_back ~1.8 m/s: measure from stride length / cycle time and
report actual values; feet must not slide when played at that speed.

## Metadata sidecar `game/assets/characters/anim_meta.json`

```json
{
  "fps": 30,
  "animations": {
    "sword_1": {"length": 0.6, "loop": false, "hits": [[0.22, 0.32]], "cancel_after": 0.42, "combo_window": [0.35, 0.75]},
    "bow_release": {"length": 0.5, "loop": false, "release": 0.12, "cancel_after": 0.3},
    "walk": {"length": 1.0, "loop": true, "ground_speed": 1.6, "footsteps": [0.0, 0.5]},
    "dodge_roll": {"length": 0.7, "loop": false, "iframes": [0.05, 0.45], "travel": 4.0, "footsteps": [0.55]}
  }
}
```
- `hits`: seconds (at 1.0x) where the weapon visibly sweeps through its contact arc. MUST match the keyed poses (the game
  applies damage only inside these windows). Multi-hit animations list several windows.
- `cancel_after`: earliest moment the next input may interrupt (recovery start). `combo_window`: [start, end] in which the
  next chain attack may be queued.
- `release`: projectile/spell spawn moment for casts/bow/throws. `footsteps`: foot-contact times (walk/run/strafe/dodge).
- `iframes`, `travel` for dodges (horizontal distance the roll visually covers; the game moves the capsule that far).
- Every animation in the library appears in the JSON with at least `length` and `loop`.

## Weapons (`game/assets/weapons/<name>.glb`)

`sword`, `greatsword`, `axe`, `spear`, `dagger`, `bow`, `staff`, `wand`, `shield`, `arrow`, plus aether variants
`sword_aether`, `greatsword_aether`, `staff_aether`, `wand_aether` (same silhouette family, glowing `BH_Aether` channels and a
floating crystal element). Origin at the grip center (shield: at the arm strap; arrow: its center). Long axis along Blender
+Z (blade/shaft up, pommel down); sword flat faces ±Y, edges ±X; shield face points -Y. Scale: sword 1.0 m, greatsword 1.6 m,
axe 0.8 m, spear 2.2 m, dagger 0.4 m, bow 1.3 m, staff 1.8 m, wand 0.35 m, shield 0.9 m tall. Distinct silhouettes; staff
with a crystal head, wand slender with a gem, bow recurve with string. 600–4000 tris each.

## Phase A deliverables (this assignment)

1. Working pipeline: `build.py` regenerates everything (`all`, `weapons`, `meta`, or a character name) + README with commands.
2. `knight.glb`, `mage.glb` with the full animation library; all weapon GLBs; `anim_meta.json` with measured values.
3. Evidence in `work/lemondev/bh-002/evidence/characters/`: EEVEE renders (1024 px) of each hero front + 3/4 + back; each hero
   holding its starting weapons (knight: sword + shield; mage: staff); contact sheets of every attack at its hit time
   (per weapon, 4 chain attacks + heavy); locomotion contact sheet; idle variants; hit/stagger/knockback/death poses; weapons
   sheet; `validation.txt` from re-importing each GLB into a fresh Blender scene (bones, animation count + names, triangles,
   materials; asserts the full skeleton and the full library exist).
4. Your own honest self-review: list what looks weak (silhouette, deformation, sliding feet, stiff poses) and fix the worst
   before reporting. Report actual measured ground speeds, triangle counts, animation count, build time.

Phase B (enemies, NPCs, a quadruped beast) will be assigned afterwards on the same pipeline — keep the body/armor/animation
code modular (per-character modules, shared rig + action library) so enemy bodies with different proportions (2.4 m brute,
4.2 m boss) can reuse the same action set via rotation-only retargeting.
