# bh-029 NPC model brief (Builder N1) — Terax and the people of Agdao

You build six townsfolk models for the Godot 4.7 game Beyond Heroes (`A:\Python\beyond-heroes`) for its new island,
**Zarael**. Read `work/lemondev/bh-029/contract.md` first (story, theme, house rules) and the shared rules in
`work/lemondev/bh-029/brief_models.md` (tools, validation, evidence, "Rules" section — they apply to you too, with
`n1` in place of `m<n>`: scratch dir `work/lemondev/bh-029/scratch/n1/`, evidence dir `work/lemondev/bh-029/evidence/npcs/`).

## Pipeline
Townsfolk use the town kit: `tools/blender/characters/town_matron.py` (the `Kit`, `TOWN_CLIPS`, `BASE_COLORS`, `pal`),
with siblings `town_officer.py`, `town_elder.py`, `town_scholar.py`, `town_fisher.py`, `town_smith.py`,
`town_merchant.py`, `town_traveler.py` as references. A module `tools/blender/characters/town_<id>.py` builds
`game/assets/characters/<id>.glb` (check `build.py` / `build_chars.py` / `README.md` for how town modules are discovered
and named, and build ONE character at a time, e.g. `build.py -- town_<id>` or whatever the existing pattern is —
never `-- all`). Copy a sibling's `.glb.import` (e.g. `officer.glb.import`), change only paths, delete the `uid=` line.
`CLIPS_ONLY = list(K.TOWN_CLIPS)` (same clip set as every townsperson — the game plays `idle`, `idle_look`, `walk`, `talk`…).
Budget ≤ 15k triangles each, natural height 1.65–1.9 m. `TINTABLE = ("BH_Cloth_Primary",)` like the others.

## Look (Zarael, visual only — no real-culture names)
Agdao is a city of stepped stone terraces with ancient engineering: inlaid wire, glyph bands, jade and turquoise.
Clothing: woven cotton in ochre, cream, teal and brick red with stepped-fret borders, quilted vests, feathered or beaded
ornaments, sandals or wrapped boots, jade and turquoise jewellery, copper wire bracelets. **Any glow is PURE WHITE**
(`BH_Emissive` albedo and emission (1,1,1)) — the user asked for white glows everywhere on Zarael. Glow should be small
(wire bracelets, a lamp, a tool tip), never the dominant read. Faces and skin: varied, warm brown tones; adults with
weathered, lived-in looks. They must read at the high gameplay camera (≈50–55° pitch, 16–26 m) — silhouette first.

Match the portraits in `game/assets/ui/portraits/{terax,wirekeeper,ilsa,agdao_porter,agdao_vendor,agdao_elder}.svg`
(rasterize them with PIL/cairosvg or a browser if you need to look) for hair, build and colour notes where they show them.

| id (module `town_<id>.py`, GLB `<id>.glb`) | Who | Look |
|---|---|---|
| `terax` | Terax, Warden of Agdao (the lead NPC; greets the hero at the pier, fought beside Aljay in the Vaults) | a seasoned warrior-guard, broad-shouldered: quilted cotton armour vest (cream/ochre) with a stepped-fret border, a short feathered shoulder cape (teal `BH_Feather`-like greens), bronze arm-guards, a jade pendant, a long spear or a sheathed obsidian-edged sword on the back/hip (rigid), a scar; hair matched to the portrait. Must look like a leader, distinct from any existing townsperson. |
| `wirekeeper` | Wirekeeper Halvessa Orn, keeper of the Heartwire (top of the Crown of Steps) | an older woman scholar-engineer: long layered robe (deep teal + cream) with fret hems, a short turquoise mosaic collar, copper wire coiled round both forearms glowing faintly white, a satchel of tools, a staff-like wire gauge (rigid, white-glowing tip), grey hair in a high bound knot. |
| `ilsa` | Captain Ilsa Rhondar of the Sunwake (the ship) | a sea captain: long sea-blue coat over a cream shirt, a wide sash, boots, a short sword at the hip, a brass spyglass at the belt, hair tied back, a weathered face. |
| `agdao_porter` | porters, lift engineers, scouts (Toma Kettridge, Quillan Ashby) | a working man: sleeveless quilted vest, wrapped trousers, a leather tool belt with a wrench/hammer, a coil of copper wire over one shoulder, headband. |
| `agdao_vendor` | traders (Dorrit Vask, Brisa Kettle, Sorrel) | a trader: tunic with fret border (`BH_Cloth_Primary`, tinted per NPC), apron, bead necklaces, a woven shoulder bag, headwrap. |
| `agdao_elder` | elders and healers (Mother Ysenne, Speaker Caius Wend) | an elder: long cream mantle over a coloured robe (`BH_Cloth_Primary`), a jade ear spool look done as simple discs, a feathered collar, a carved walking staff (rigid). Slightly stooped. |

## Deliver
Six modules, six GLBs + `.import`, evidence under `work/lemondev/bh-029/evidence/npcs/` (`<id>.md`, `<id>_rest_iso.png`,
`<id>_clips.png` or a front/back preview). Validate import on a scratch copy (never Godot on `game/`). Final message: a
concise per-model report (id, files, triangles, height, materials/palette, limitations).
