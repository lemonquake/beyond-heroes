# bh-029 T1 — Zarael textures, portraits, atlas

All procedural (numpy / scipy / PIL; SVG for portraits), deterministic, no third-party images, no lettering.
Previews were rendered offline (numpy shading for textures, resvg for the SVGs); Godot was not run.

## 1. Texture sets — `tools/textures/gen_zarael_textures.py`
`python tools/textures/gen_zarael_textures.py [set ...]` → `game/assets/textures/<set>_{albedo,normal,rough}.png`
(1024², tileable, OpenGL +Y normal from a height field exactly as `gen_textures.py`, linear roughness) and a `.import`
beside each PNG (copied from `sunstone_*`, `uid=` removed, `.godot/imported` hash = md5 of the res:// path).

| set | look | suggested world tile | mean albedo (sRGB) | luma | sat | rough |
|---|---|---|---|---|---|---|
| glyph_stone | pale limestone, irregular running bond (6 courses); courses 1 and 4 are carved bands (stepped fret / glyph cartouches + fret) in relief; chips, faint lichen, damp streaks | 2 m | 0.49 0.47 0.42 | 0.47 | 0.15 | 0.86 |
| jade_stone | polished jade slabs (4 rows x 3), soft cloudy body, pale veins, gold wire inlay in dark grout | 2 m | 0.25 0.33 0.28 | 0.30 | 0.26 | 0.20 |
| obsidian | black glass flags, conchoidal ripple shells, hairline fractures, thin molten-copper seams | 2–3 m | 0.07 0.06 0.07 | 0.07 | 0.16 | 0.14 |
| lime_plaster | warm off-white plaster: trowel swaths with edge ridges, hairline cracks, flaked patches showing stone | 2 m | 0.61 0.58 0.54 | 0.58 | 0.11 | 0.88 |
| terrace_paving | fitted irregular flags, two square incised glyph tiles, one horizontal + one vertical inlaid wire line per tile, grit in joints | 3–4 m | 0.45 0.41 0.36 | 0.42 | 0.20 | 0.81 |
| turquoise_mosaic | ~1150 irregular turquoise/teal tesserae, matrix webs, ~3 % shell-white, ~2 % red, dark grout | 0.75–1 m | 0.25 0.35 0.33 | 0.32 | 0.31 | 0.49 |
| jungle_floor | dark loam, broad fallen leaves (veins, decay holes), roots, seeds, moss patches | 3 m | 0.24 0.20 0.13 | 0.20 | 0.44 | 0.85 |
| red_clay | packed red-ochre clay, crack network with curled plate edges, pebbles, leaning dry-grass tufts | 4 m | 0.43 0.32 0.25 | 0.34 | 0.41 | 0.90 |
| blackwire_soil | cracked dark red-brown earth, thin dim violet-red veins along the big cracks, glassy grit + rare glints | 4 m | 0.21 0.14 0.12 | 0.16 | 0.40 | 0.87 |
| cliff_ochre | 15 warped strata (hard ledges with lit lips / shaded undersides, soft recessed beds), cross-bedding, per-bed vertical joints, erosion streaks | 6–8 m | 0.44 0.34 0.27 | 0.37 | 0.39 | 0.89 |

Seam scores (albedo/normal) are in `seam_report.txt`; all sets are periodic by construction. The two "outliers"
(jade_stone y 1.79, glyph_stone y 0.67) are only because a course joint sits exactly on the tile edge.
Albedos are mid-value and desaturated; obsidian is deliberately dark (black glass), lime_plaster deliberately light
(the game tints it ochre/red for `BH_LimePlaster` / `BH_LimePlasterRed`). Veins/wires are dim albedo only — no emission.

Material mapping (contract): BH_GlyphStone / BH_GlyphStoneDark → glyph_stone (darken + moss tint for Dark),
BH_Jade → jade_stone, BH_Obsidian → obsidian, BH_LimePlaster(Red) → lime_plaster, BH_TerracePave → terrace_paving,
BH_Turquoise → turquoise_mosaic; terrain: jungle_floor, red_clay, blackwire_soil, cliff_ochre, terrace_paving.

Evidence: `sheet.png` — per set: albedo 2x2 | lit 2x2 plane (normal + rough) | lit sphere | normal 2x2 / rough 2x2.
Revisions: (1) first pass; (2) band-limited domain warps (texlib's warp frays joints), softer jade, bigger plaster
flakes + trowel ridges, incised paving glyphs, fewer white/red tesserae, sparser jungle leaves, visible clay /
blackwire crack networks; (3) cliff ledges made bimodal and shaded, crack warps de-folded, jade pepper spots removed,
deeper glyph carving.

## 2. Portraits — `tools/ui_art/bh029_portraits.py`
`python tools/ui_art/bh029_portraits.py` (needs resvg-py only for the preview) → `game/assets/ui/portraits/`
`terax.svg, wirekeeper.svg, ilsa.svg, agdao_porter.svg, agdao_vendor.svg, agdao_elder.svg` + `.svg.import` (copied from
`lape.svg.import`, no uid). 256x256, the bh-002 painted-bust helpers, frame and ThorVG-safe subset. Previews:
`portraits.png`, `portraits_512.png`. Revision 2 replaced Terax's radial feather fan with an upright helm plume and
rebuilt the bronze gauntlet as a fist on a wire-wound vambrace; the Wirekeeper's coils got glowing wire bands.

## 3. Zarael atlas — `tools/ui_art/bh029_atlas.py`
`python tools/ui_art/bh029_atlas.py` → `game/assets/ui/atlas/zarael_atlas.png` (2000x1700 RGB, no text/roads/markers)
+ `.import` (from salmonan_atlas, no uid). `atlas_regions.png` = the painting with region boxes (labels in evidence only).

Region centres in the 1000 x 850 atlas space (painted footprint boxes x0,y0,x1,y1):

| map | centre | box |
|---|---|---|
| agdao | (194, 600) | (94, 488, 294, 700) — Crown of Steps pyramid at (194, 574), quay/piers into the bay at ~(190, 666–700) |
| zr_coilwood | (330, 404) | (150, 268, 480, 560) |
| zr_barrens | (548, 488) | (452, 372, 650, 640) — fallen colossus at ~(592, 452) |
| bridge_of_death | (690, 318) | (632, 300, 750, 336) — span painted west→east from x 640 to 744 at y 318 |
| zr_citadel | (838, 352) | (760, 268, 920, 440) — walls centred (842, 350) |

Gorge: meanders north→south coast to coast along x ≈ 660–712, narrowest (~26 px) at the bridge, ~45–60 px elsewhere.
