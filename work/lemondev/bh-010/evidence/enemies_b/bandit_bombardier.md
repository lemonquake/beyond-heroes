# bandit_bombardier: Bandit Bombardier (bh-010, Builder B)

- Module: `tools/blender/characters/enemy_bandit_bombardier.py`. GLB: `game/assets/characters/bandit_bombardier.glb` (3.1 MB, 46 clips, clip lengths verified, see build_log.txt)
- Height: 1.78 m rest, 1.77 m idle. Width 1.70 m in T-pose.
- Tris: 14,762 (7,762 verts, 174 parts)
- Attack clips: cast_quick, cast_heavy, dagger_1, shield_bash, plus the ENEMY_BASE_CLIPS set
- Palette (`bandit_bombardier`): leather apron/gloves/boots, lighter horn-leather straps, faded red bandana, quilted ochre padded shirt, dark trousers, red-brown beard, black-iron bombs (DarkSteel), brass goggles and bomb collars (Gold), rust keg hoops, wood keg and cudgel, steel knife. BH_Emissive = orange fuse ember only.
- Distinctness: same bandit browns and red as the Cutthroat and Marksman. The silhouette differs through the powder keg hump on the back with a lit fuse, a wider stocky body, the apron and the bomb bandolier. See the lineup tiles in bandit_bombardier_rest_iso.png.
- Deformation (bandit_bombardier_audit.txt): worst stretch 2.16x (thigh.L, apron/leg seam), dL 10.9 cm. Cutthroat baseline is 2.19x / 8.4 cm (baseline_bandit_cutthroat_audit.txt). The lower apron is split into leg panels bound to the thighs.
- Evidence: bandit_bombardier_rest_iso.png, bandit_bombardier_clips.png (idle, 4 attacks, hit_heavy, death_back), bandit_bombardier_audit.txt
- Limitations: no shield prop, so shield_bash is played empty-handed on the left. Death clips dip up to 0.35 m below z=0 (the library clip lies the body down; the same happens on other enemies).
