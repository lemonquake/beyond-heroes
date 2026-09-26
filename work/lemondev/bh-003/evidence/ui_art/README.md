# bh-003 UI art — Builder F evidence

Rebuild everything with `python tools/ui_art/bh003_build.py`. It needs `pip install resvg-py fonttools pillow`: fontTools turns the letters and mottos into glyph outlines at build time, and resvg makes the PNGs.

**Rasteriser note:** Godot was not run. All evidence PNGs and the two banner PNGs are rendered with **resvg** (Rust SVG renderer, via `resvg-py`), not with Godot's ThorVG. The SVGs use only the ThorVG-safe subset of `bh_svg.py`: svg, defs, linear/radialGradient, stop, g, path, circle, ellipse and rect. There is no `<text>`, filter, mask, clip or style. `subset_check.txt` records the check for every file. Nobody has yet seen these files through Godot's importer.

## Generator code (new; existing toolkit imported, not modified)
| file | purpose |
|---|---|
| `tools/ui_art/bh003_text.py` | text → SVG path outlines (DejaVu Serif Bold for tier letters, Liberation Serif Bold for mottos) |
| `tools/ui_art/bh003_render.py` | resvg rasteriser + PIL contact-sheet helper |
| `tools/ui_art/bh003_tiers.py` | 9 tier emblems |
| `tools/ui_art/bh003_guilds.py` | 2 banners, 2 crests, PNG cloth-texture variant |
| `tools/ui_art/bh003_portraits.py` | 13 NPC portraits (uses the `portraits.py` bust helpers) |
| `tools/ui_art/bh003_build.py` | writes all outputs + evidence; refuses to overwrite the 8 pre-existing portraits |

## Outputs
**Tier emblems:** these live in `game/assets/ui/tiers/` (viewBox 0 0 128 128) and are named `tier_<key>.svg`, matching `data_guilds.gd` `EMBLEM`.
- `tier_unranked.svg`: hollow grey ring with a dash
- `tier_e.svg`: dark iron ring-shield with 10 rivets, dull grey
- `tier_d.svg`: bronze kite shield
- `tier_c.svg`: silver crest with one star above
- `tier_b.svg`: gold shield wrapped in gold laurel branches, red tie
- `tier_a.svg`: eight-point azure star with a silver edge and glow
- `tier_s.svg`: crimson and gold sunburst
- `tier_ss.svg`: two violet-silver crescent moons over a dark star-field disc
- `tier_sss.svg`: radiant cyan-white Aether crown with prismatic rays and orbs; the letters sit on the crown band

**Guilds:** these live in `game/assets/ui/guilds/`.
- `swordfin_banner.svg` (256×384): sea-blue swallow-tailed banner on a rod, silver trim. A silver marlin leaps over two crossed blades. The motto ribbon reads "STRIKE FIRST. / STRIKE TRUE." on two lines.
- `lantern_banner.svg` (256×384): dusk-violet cloth with gold trim. A golden lantern holds an eye-shaped flame. The motto reads "WE KEEP THE LIGHT".
- `swordfin_crest.svg` and `lantern_crest.svg` (128×128) are round medallion versions of the same symbols.
- `swordfin_banner.png` and `lantern_banner.png` (512×768 RGBA) are the **cloth-only** texture variant, meant for 3D cloth meshes. They have the same art, but there is no rod, hook or tassels, and the cloth fills the full width. The swallowtail notch is transparent.

**Portraits:** these live in `game/assets/ui/portraits/` (256×256). All 13 are new, and no existing file was touched:
- `innkeeper`: Hesta, tan skin, red polka-dot headscarf, apron, dishcloth, big smile, lamplight
- `bard`: Fennick, curly hair, red feathered cap, teal doublet, lute neck and pegbox
- `fisher`: Old Marrow, old skin, oilskin sou'wester, deep wrinkles, white stubble, grey eyes
- `veteran`: Venna Kail, pale skin, cropped grey hair, scar across the brow, azure star pin, battered pauldron
- `swordfin_master`: Rhea Talvanne, high bun, blue coat with silver frogging, swordfish pin, spear
- `swordfin_quartermaster`: Dax Harrowby, broad jaw, black beard with a grey streak, open ledger, blue sash
- `lantern_master`: Oren Vale, bald with white tufts, gold round spectacles, violet robe with gold stole, hand lantern
- `lantern_scribe`: Lio Sanvar, young, freckles, ink smudge, quill behind the ear, violet tunic
- `netmender`: Tessaly, long braid, shell earrings, fishing net with floats over the shoulder
- `cartographer`: Aurand Quell, receding hair with grey temples, mustache, magnifying lens, rolled maps
- `widow`: Ilvena Hald, grey veil and dress, sorrowful brows, soldier's tag on a cord
- `keeper`: Thadric Moll, shaved head, shrine mark, wooden prayer beads, bestiary tome with a beast-eye sigil
- `refugee`: Zerin Ven, ash-dusted hooded travel cloak, tired eyes, soot smudge, ember light

## Evidence files (this folder)
- `tiers_28.png`, `tiers_48.png`, `tiers_128.png`: emblems at each size
- `tiers_28_light.png`: the 28 px emblems on a light background
- `tiers_28_zoom4x.png`: the 28 px renders blown up 4× with nearest-neighbour, to check the letters
- `tiers_hud_mock.png`: each emblem at 28 px next to a "Lv" label
- `guild_banners.png`: both banner SVGs, and both PNG textures shown at 50%
- `swordfin_banner_512.png`, `lantern_banner_512.png`: the banner SVGs at 512 px wide
- `guild_crests.png`: the crests at 28, 48 and 128 px
- `portraits_64.png`, `portraits_128.png`, `portraits_256_a.png`, `portraits_256_b.png`: the new portraits
- `portraits_all_128.png`: the new portraits next to the 8 existing ones, to compare style
- `subset_check.txt`: the SVG subset check; all 26 SVGs pass

## Known issues
- None of this has been rendered through Godot/ThorVG, only through resvg. Godot will create the `.import` files on the next editor import; none are included here.
- At 28 px, the SS and SSS letters are readable but small. SSS is the tightest: three letters are squeezed onto the crown band. E through S read clearly.
- The guild crests at 28 px show only the colour scheme and a rough silhouette. The swordfish and the lantern details become clear from about 48 px.
- The banner PNGs are the cloth-only variant, not a pixel copy of the SVG: they have no rod, hook or tassels. If an exact raster of the SVG is wanted instead, change `banner_png_svg` in `bh003_guilds.py`.
- Skin tones use only the four existing palettes (SKIN, SKIN_TAN, SKIN_OLD, SKIN_PALE). Faces are told apart by head shape, hair, age marks and costume, so several people share a palette.
- The build depends on `resvg-py` and `fonttools` (pip). Neither was present before this run; I installed both.
