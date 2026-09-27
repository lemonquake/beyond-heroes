# shadowblade (bh-010)

- GLB: `game/assets/characters/shadowblade.glb` (7.8 MB), module `tools/blender/characters/char_shadowblade.py`
- Height (rest mesh bbox, hood peak): 1.876 m. Same skeleton / proportions / rest pose as knight and mage.
- Tris: 19,864 (145 parts). One skinned mesh.
- Bones: 27 = 24 standard + extra `scarf.1`, `scarf.2` (chest, scarf tails down the back) and `sash.1` (hips, sash
  tail on the left hip). secondary() hangs them toward gravity, streams them back with ground speed and adds a
  step-rate flutter (derived from evaluated frames, loops stay seamless).
- Clips: 123 (full shared library + `idle_shadowblade`, 3.5 s, non-looping, props R=dagger).
- Weapons: none modeled in hand; attach at runtime to `weapon.R` / `weapon.L`.
- Look: quilted dark leather vest over a dark tunic, crossed chest straps with throwing knives around a silver ring,
  layered dark-steel pauldron on the left shoulder only, tassets on the right hip, low belt with front/back flaps,
  sheathed knife on the left thigh, deep hood with shadowed lining and a dull-silver edge trim, cloth mask over the
  lower face, subtle violet eyes (`BH_Emissive`, strength 3), long tattered scarf and waist sash, wrapped forearms,
  dark-steel knuckle gloves, soft wrapped boots.
- Tintable: `BH_Cloth_Primary` (scarf + sash), exported without suffix; class tint violet Color(0.45, 0.2, 0.6).
- Palette (`BH_*__shadowblade`): Cloth_Secondary charcoal (0.05,0.046,0.06), Leather (0.028,0.026,0.032),
  LeatherDark (0.014,0.013,0.017), Mask deep violet-grey (0.075,0.055,0.095), Wrap (0.12,0.11,0.13), DarkSteel metal
  (0.075,0.075,0.085), Steel dull silver (0.36,0.36,0.38), Skin, Hair, Shadow, Emissive violet (0.62,0.3,1.0).
- idle_shadowblade: tosses the dagger end over end (two turns) and catches it, flips it to reverse grip, rolls the
  neck and shoulders, sinks into a low ready crouch, rises and flips it back. The spin is a rotation of the weapon
  socket; the dagger never leaves the hand bone.
- Evidence: `shadowblade_turnaround.png`, `shadowblade_clips.png`, `heroes_lineup_iso.png`, `build_log.txt`,
  `shadowblade_info.json`.
