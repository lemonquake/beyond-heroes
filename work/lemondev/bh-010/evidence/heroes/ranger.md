# ranger (bh-010)

- GLB: `game/assets/characters/ranger.glb` (7.3 MB), module `tools/blender/characters/char_ranger.py`
- Height (rest mesh bbox): 1.849 m. Same skeleton / proportions / rest pose as knight and mage.
- Tris: 22,270 (282 parts). One skinned mesh.
- Bones: 24 (standard skeleton). Extra bones: none. No secondary() motion.
- Clips: 123 (full shared library + `idle_ranger`, 3.5 s, non-looping, props L=bow).
- Weapons: none modeled in hand; attach at runtime to `weapon.R` / `weapon.L`.
- Look: short dagged mantle over the shoulders, hood down at the nape, fur collar, layered leather jerkin with laced
  front and tan chest plates, split skirt, pouch belt, hunting knife on right hip, signal horn on left, archery bracer
  on the left forearm, wraps on the right, fingerless gloves, wrapped trousers, soft high laced boots, quiver of
  fletched arrows diagonally on the back (mouth over the right shoulder). Rugged bare face with stubble, hair tied back.
- Tintable: `BH_Cloth_Primary` (mantle), exported without suffix; class tint green Color(0.3, 0.55, 0.28).
- Palette (`BH_*__ranger`): Cloth_Secondary moss (0.045,0.05,0.032), Leather brown (0.13,0.07,0.036), LeatherDark
  (0.05,0.03,0.018), Horn tan (0.30,0.20,0.11), Fur (0.15,0.10,0.06), Wrap linen (0.16,0.15,0.105), Bone
  (0.62,0.57,0.45), Wood (0.2,0.12,0.06), Bronze metal (0.42,0.27,0.12), Steel, Skin, Hair, Shadow, EyeWhite.
- idle_ranger: shades the eyes, scans left and right, then reaches over the right shoulder, draws an arrow halfway
  from the quiver and slides it back; bow held low in the left hand.
- Evidence: `ranger_turnaround.png`, `ranger_clips.png`, `heroes_lineup_iso.png`, `build_log.txt`, `ranger_info.json`.
